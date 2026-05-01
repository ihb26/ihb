import json
import litellm
import uuid
from litellm import completion
from litellm.types.utils import Choices, Message
from typing import Any

from .config import ModelConfig
from .dsl.predicates.predicate_types import Context
from .logger import get_logger
from .models.prompt import Prompt
from .models.tool_call import ToolCall
from .resilience import run_with_retries
from .utils import get_run_id, is_langfuse_configured


logger = get_logger(__name__)


class Client:
    def __init__(
        self,
        timeout: int,
        max_retries: int,
        enable_langfuse: bool,
        max_chat_iters: int
    ):
        self.trace_user_id = f"ihb-run-{get_run_id()}"
        if enable_langfuse and is_langfuse_configured():
            self.enable_langfuse = enable_langfuse
            logger.debug(f"Langfuse Run/User ID: {self.trace_user_id}")
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]
        else:
            self.enable_langfuse = False
            logger.debug("Not using Langfuse")
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_chat_iters = max_chat_iters
    
    def _try_run_completion(
        self,
        prompt: Prompt,
        model: ModelConfig,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any]
    ) -> Choices:
        def _call() -> Choices:
            extra_body: dict[str, Any] = {}
            
            thinking: bool | None = None
            if model.thinking is not None:
                if model.via_chat_template_kwargs:
                    extra_body["chat_template_kwargs"] = { "enable_thinking": model.thinking }
                else:
                    thinking = model.thinking
            
            if model.skip_special_tokens is not None:
                extra_body["skip_special_tokens"] = model.skip_special_tokens

            kwargs = {}
            if "bedrock" not in model.name:
                kwargs["extra_body"] = extra_body
            
            response = completion(
                model.name,
                base_url=model.base_url,
                messages=messages,
                tools=prompt.get_tools(),
                tool_choice=("auto" if prompt.tools else None),
                temperature=model.temperature,
                reasoning_effort=model.reasoning_effort,
                thinking=thinking,
                metadata=metadata,
                timeout=self.timeout,
                max_completion_tokens=model.max_completion_tokens,
                drop_params=True,
                allowed_openai_params=["tools", "tool_choice"],
                **kwargs
            )
            return response.choices[0]
        
        return run_with_retries(
            _call,
            max_retries=self.max_retries,
            msg_err=f"Max retries ({self.max_retries}) reached while trying to call model"
        )
    
    def run_prompt_for_model(
        self,
        prompt: Prompt,
        model: ModelConfig
    ) -> tuple[Context, list[Message | dict[str, Any]]]:
        metadata = {
            "session_id": str(uuid.uuid4()),
            "trace_user_id": self.trace_user_id,
            "tags": [
                "ihb",
                f"{prompt.category}_{prompt.subcategory}",
                prompt.name,
                model.name,
            ],
        }

        if prompt.user_prompt is not None and type(prompt.user_prompt) == str:
            content_user = []
            if prompt.user_prompt is not None:
                content_user.append({ "type": "text", "text": prompt.user_prompt })
            if prompt.user_image_path is not None:
                content_user.append({ "type": "image_url", "image_url": prompt.get_user_image() })
            
            messages = [
                { "role": "system", "content": prompt.system_prompt },
                { "role": "user", "content": content_user },
            ]
        elif prompt.user_prompt is not None:
            messages = [
                { "role": "system", "content": prompt.system_prompt },
            ]

            messages.extend(prompt.user_prompt)

        ctx_content: str = ""
        ctx_tools: list[ToolCall] = []

        max_chat_iters = self.max_chat_iters
        if prompt.max_chat_iters is not None:
            max_chat_iters = prompt.max_chat_iters
        
        for _ in range(max_chat_iters):
            choice = self._try_run_completion(prompt, model, messages, metadata)
            finish_reason = choice.finish_reason
            message = choice.message
            messages.append(message)

            logger.debug(f"({model.name}) {finish_reason=} {message=}")
            if finish_reason in ("stop", "length"):
                ctx_content += message.content
                break
            elif finish_reason in ("tool_calls", "function_call"):
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args: dict[str, Any] = json.loads(tool_call.function.arguments)
                        tool_response = prompt.get_tool_response(tool_name, tool_args)

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_response,
                        })

                        ctx_tool = ToolCall(tool_name, tool_args, tool_response)
                        ctx_tools.append(ctx_tool)
                    
                if prompt.break_on_tool_call:
                    break
            else:
                break

        return (Context(ctx_content, ctx_tools), messages)
