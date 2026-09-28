import copy
import json
import litellm
import uuid
from litellm import completion
from litellm.types.utils import (
    ChatCompletionMessageCustomToolCall,
    Choices,
    Message,
)
from typing import Any

from .config import DefensesConfig, ModelConfig
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
        max_chat_iters: int,
        kv_text: bool = False,
        kv_mag: float | None = None
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
        self.kv_text = kv_text
        self.kv_mag = kv_mag
    
    def _try_run_completion(
        self,
        prompt: Prompt,
        model: ModelConfig,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any]
    ) -> tuple[Choices, tuple[int, int]]:
        def _call() -> tuple[Choices, tuple[int, int]]:
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
            
            if self.kv_text and (self.kv_mag is not None) and prompt.kv_text:
                kwargs["extra_headers"] = {
                    "X-KV-Intervention-Texts": json.dumps([prompt.kv_text]),
                    "X-KV-Intervention-Multiplier": str(self.kv_mag),
                }

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

            n_inp_tokens = 0
            n_out_tokens = 0
            try:
                if hasattr(response, "usage"):
                    usage = response.usage
                    if hasattr(usage, "prompt_tokens"):
                        prompt_tokens = usage.prompt_tokens
                        if isinstance(prompt_tokens, int):
                            n_inp_tokens += prompt_tokens
                    if hasattr(usage, "completion_tokens"):
                        completion_tokens = usage.completion_tokens
                        if isinstance(completion_tokens, int):
                            n_out_tokens += completion_tokens
                    logger.debug(f"{model.pretty_name}: {n_inp_tokens=} {n_out_tokens=}")
            except:
                logger.debug(f"{model.pretty_name}: could not parse token usage", exc_info=True)

            return (response.choices[0], (n_inp_tokens, n_out_tokens))
        
        return run_with_retries(
            _call,
            max_retries=self.max_retries,
            msg_err=f"Max retries ({self.max_retries}) reached while trying to call model"
        )
    
    def run_prompt_for_model(
        self,
        prompt: Prompt,
        model: ModelConfig,
        defenses: DefensesConfig | None
    ) -> tuple[Context, list[dict[str, Any]], tuple[int, int]]:
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

        if defenses is not None:
            prompt = copy.deepcopy(prompt)
            prompt.apply_defences_to_hardcoded_tool_responses(defenses)

        if (prompt.user_prompt is not None) and isinstance(prompt.user_prompt, str):
            content_user = []
            if prompt.user_prompt is not None:
                content_user.append({ "type": "text", "text": prompt.user_prompt })
            if prompt.user_image_path is not None:
                content_user.append({ "type": "image_url", "image_url": prompt.get_user_image() })
            
            messages: list[dict[str, Any]] = [
                { "role": "system", "content": prompt.system_prompt },
                { "role": "user", "content": content_user },
            ]
        elif prompt.user_prompt is not None:
            messages: list[dict[str, Any]] = [
                { "role": "system", "content": prompt.system_prompt },
            ]

            messages.extend(prompt.user_prompt)

        ctx_content: str = ""
        ctx_tools: list[ToolCall] = []

        max_chat_iters = self.max_chat_iters
        if prompt.max_chat_iters is not None:
            max_chat_iters = prompt.max_chat_iters
        
        total_n_inp = 0
        total_n_out = 0

        for _ in range(max_chat_iters):
            choice, (n_inp, n_out) = self._try_run_completion(prompt, model, messages, metadata)
            finish_reason = choice.finish_reason
            message = choice.message
            messages.append(message.json())

            total_n_inp += n_inp
            total_n_out += n_out

            logger.debug(f"({model.name}) {finish_reason=} {message=}")
            if finish_reason in ("stop", "length"):
                should_break = True
                if message.content:
                    ctx_content += message.content
                elif hasattr(message, "reasoning_content") and message.reasoning_content:
                    # ctx_content += message.reasoning_content
                    should_break = False
                if should_break:
                    break
            elif finish_reason in ("tool_calls", "function_call"):
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        if isinstance(tool_call, ChatCompletionMessageCustomToolCall):
                            tool_name = tool_call.custom.name
                            tool_args: dict[str, Any] = json.loads(tool_call.custom.input)
                        else:
                            tool_name = tool_call.function.name
                            tool_args: dict[str, Any] = json.loads(tool_call.function.arguments)
                            assert tool_name is not None, "Model called tool without a name"
                        
                        tool_response = prompt.get_tool_response(tool_name, tool_args)

                        if defenses and defenses.spotlighting and defenses.spotlighting_format is not None:
                            tool_response = defenses.spotlighting_format.format(tool_response=tool_response)

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

        return (Context(ctx_content, ctx_tools), messages, (total_n_inp, total_n_out))
