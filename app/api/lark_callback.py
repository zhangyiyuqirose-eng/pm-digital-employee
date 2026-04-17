"""
PM Digital Employee - Lark Callback
PM Digital Employee System - Lark interactive card callback handler

Handles user interactions from Lark interactive cards (button clicks,
form submissions, etc.) and updates cards accordingly.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.logging import get_logger, set_trace_id
from app.core.rate_limiter import limiter
from app.integrations.lark.schemas import LarkCardBuilder
from app.integrations.lark.service import get_lark_service
from app.services.idempotency_service import get_card_callback_idempotency_service

logger = get_logger(__name__)

router = APIRouter(prefix="/lark/callback", tags=["Lark Callback"])


@router.post("/card")
@limiter.limit("200/minute")
async def receive_card_callback(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Receive Lark card callback.

    When a user clicks a button on an interactive card, Lark pushes
    a callback to this endpoint.

    Args:
        request: FastAPI request object
        background_tasks: Background task runner

    Returns:
        Dict: Response result (can include updated card template)
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        data = json.loads(body_str)

        # Handle URL verification challenge
        if "challenge" in data:
            logger.info("Lark callback URL challenge verification received")
            return {"challenge": data["challenge"]}

        # Parse callback data
        header = data.get("header", {})
        event = data.get("event", {})

        callback_id = header.get("event_id", "")
        action = event.get("action", {})
        value = event.get("value", {})

        # Extract user info
        user_id = event.get("user", {}).get("user_id", {}).get("open_id", "")
        token = event.get("token", "")

        # Set trace_id
        trace_id = f"card:{callback_id}:{user_id}"
        set_trace_id(trace_id)

        logger.info(
            "Lark card callback received",
            callback_id=callback_id,
            user_id=user_id,
            action_type=action.get("type", ""),
        )

        # Handle action trigger (button click)
        if action.get("type") == "button":
            button_value = action.get("value", {})
            return await _handle_button_click(
                callback_data=data,
                button_value=button_value,
                user_id=user_id,
                token=token,
                background_tasks=background_tasks,
            )

        # Handle form submission
        if action.get("type") == "select_static" or action.get("type") == "select_person":
            selected_value = action.get("value", "")
            return await _handle_select_callback(
                callback_data=data,
                selected_value=selected_value,
                user_id=user_id,
                token=token,
                background_tasks=background_tasks,
            )

        logger.warning("Unknown callback type", action_type=action.get("type"))
        return {"code": 0, "msg": "unknown action type"}

    except json.JSONDecodeError:
        logger.error("Failed to parse callback body")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to handle callback", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")


async def _handle_button_click(
    callback_data: Dict[str, Any],
    button_value: Dict[str, Any],
    user_id: str,
    token: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Handle button click callback.

    Args:
        callback_data: Full callback payload
        button_value: Button value object
        user_id: User open_id
        token: Callback token
        background_tasks: Background task runner

    Returns:
        Dict: Response with optional card update
    """
    callback_id = callback_data.get("header", {}).get("event_id", "")

    logger.info(
        "Handling button click",
        callback_id=callback_id,
        button_value=button_value,
        user_id=user_id,
    )

    # Idempotency check
    idempotency_service = get_card_callback_idempotency_service()
    if not await idempotency_service.check_callback(callback_id, {"button_value": button_value}):
        logger.info("Card callback already processed", callback_id=callback_id)
        return _build_already_processed_response()

    # Async processing
    background_tasks.add_task(
        _process_button_click_async,
        button_value,
        user_id,
        token,
        callback_id,
    )

    # Return processing indicator
    return _build_processing_response()


async def _process_button_click_async(
    button_value: Dict[str, Any],
    user_id: str,
    token: str,
    callback_id: str,
) -> None:
    """
    Async button click processing.

    Args:
        button_value: Button value object
        user_id: User open_id
        token: Callback token
        callback_id: Callback event ID
    """
    set_event_id(callback_id)

    idempotency_service = get_card_callback_idempotency_service()

    try:
        logger.info(
            "Processing button click async",
            callback_id=callback_id,
            button_value=button_value,
        )

        # Parse action from button value
        # Format: {"action": "confirm:skill_name"} or {"action": "cancel"}
        action = button_value.get("action", "")

        # Parse action type and value
        if ":" in action:
            action_type, action_value = action.split(":", 1)
        else:
            action_type = action
            action_value = ""

        # Dispatch by action type
        if action_type == "confirm":
            result = await _handle_confirm_action(user_id, action_value)
        elif action_type == "cancel":
            result = await _handle_cancel_action(user_id)
        elif action_type == "select_project":
            result = await _handle_select_project_action(user_id, action_value)
        elif action_type == "update_task":
            result = await _handle_update_task_action(user_id, action_value)
        elif action_type == "acknowledge_risk":
            result = await _handle_acknowledge_risk_action(user_id, action_value)
        elif action_type == "approve":
            result = await _handle_approve_action(user_id, action_value)
        elif action_type == "reject":
            result = await _handle_reject_action(user_id, action_value)
        elif action_type == "retry":
            result = await _handle_retry_action(user_id, action_value)
        # 数据录入菜单按钮处理
        elif action_type == "menu_task":
            result = await _handle_menu_task_action(user_id, action_value)
        elif action_type == "menu_risk":
            result = await _handle_menu_risk_action(user_id, action_value)
        elif action_type == "menu_cost":
            result = await _handle_menu_cost_action(user_id, action_value)
        elif action_type == "menu_milestone":
            result = await _handle_menu_milestone_action(user_id, action_value)
        elif action_type == "create_project":
            result = await _handle_create_project_action(user_id, action_value)
        elif action_type == "create_task":
            result = await _handle_create_task_action(user_id, action_value)
        elif action_type == "create_risk":
            result = await _handle_create_risk_action(user_id, action_value)
        elif action_type == "create_cost":
            result = await _handle_create_cost_action(user_id, action_value)
        elif action_type == "create_milestone":
            result = await _handle_create_milestone_action(user_id, action_value)
        else:
            logger.warning("Unknown action type", action_type=action_type)
            result = {"success": False, "error": "Unknown action type"}

        # Mark completed
        await idempotency_service.mark_callback_completed(
            callback_id,
            {"button_value": button_value},
            callback_id,
        )

        # Send result card
        lark_service = get_lark_service()
        if result.get("success"):
            await lark_service.send_success_card(
                user_id=user_id,
                title="Success",
                message=result.get("message", "Operation completed."),
            )
        else:
            await lark_service.send_error_card(
                user_id=user_id,
                error_message=result.get("error", "Processing failed."),
            )

        logger.info(
            "Button click processed",
            callback_id=callback_id,
            success=result.get("success"),
        )

    except Exception as e:
        logger.error(
            "Failed to process button click async",
            callback_id=callback_id,
            error=str(e),
        )

        # Mark failed
        await idempotency_service.mark_failed(
            event_id=callback_id,
            event_type="card_callback",
            error_message=str(e),
        )

        # Send error card
        lark_service = get_lark_service()
        await lark_service.send_error_card(
            user_id=user_id,
            error_message=str(e),
        )


async def _handle_confirm_action(
    user_id: str,
    skill_name: str,
) -> Dict[str, Any]:
    """Handle confirm action."""
    logger.info("Handling confirm action", skill=skill_name, user_id=user_id)
    # TODO: Execute skill
    return {"success": True, "message": f"Started executing {skill_name}"}


async def _handle_cancel_action(
    user_id: str,
) -> Dict[str, Any]:
    """Handle cancel action."""
    logger.info("Handling cancel action", user_id=user_id)
    return {"success": True, "message": "Operation cancelled."}


async def _handle_select_project_action(
    user_id: str,
    project_id: str,
) -> Dict[str, Any]:
    """Handle select project action."""
    logger.info("Handling select project action", project_id=project_id, user_id=user_id)
    # TODO: Bind user to project context
    return {"success": True, "message": f"Selected project: {project_id}"}


async def _handle_update_task_action(
    user_id: str,
    task_info: str,
) -> Dict[str, Any]:
    """Handle update task action."""
    logger.info("Handling update task action", task_info=task_info, user_id=user_id)
    # TODO: Call task update service
    return {"success": True, "message": "Task updated."}


async def _handle_acknowledge_risk_action(
    user_id: str,
    risk_id: str,
) -> Dict[str, Any]:
    """Handle acknowledge risk action."""
    logger.info("Handling acknowledge risk action", risk_id=risk_id, user_id=user_id)
    # TODO: Update risk status
    return {"success": True, "message": "Risk acknowledged, will continue tracking."}


async def _handle_approve_action(
    user_id: str,
    approval_id: str,
) -> Dict[str, Any]:
    """Handle approve action."""
    logger.info("Handling approve action", approval_id=approval_id, user_id=user_id)
    # TODO: Update approval status
    return {"success": True, "message": "Approval granted."}


async def _handle_reject_action(
    user_id: str,
    approval_id: str,
) -> Dict[str, Any]:
    """Handle reject action."""
    logger.info("Handling reject action", approval_id=approval_id, user_id=user_id)
    # TODO: Update approval status
    return {"success": True, "message": "Approval rejected."}


async def _handle_retry_action(
    user_id: str,
    original_action: str,
) -> Dict[str, Any]:
    """Handle retry action."""
    logger.info("Handling retry action", original_action=original_action, user_id=user_id)
    # TODO: Re-execute original action
    return {"success": True, "message": "Re-executing..."}


async def _handle_select_callback(
    callback_data: Dict[str, Any],
    selected_value: str,
    user_id: str,
    token: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Handle select callback."""
    callback_id = callback_data.get("header", {}).get("event_id", "")

    logger.info(
        "Handling select callback",
        callback_id=callback_id,
        selected_value=selected_value,
        user_id=user_id,
    )

    background_tasks.add_task(
        _process_select_async,
        selected_value,
        user_id,
        callback_id,
    )

    return _build_processing_response()


async def _process_select_async(
    selected_value: str,
    user_id: str,
    callback_id: str,
) -> None:
    """Async select processing."""
    set_event_id(callback_id)

    try:
        logger.info(
            "Processing select async",
            callback_id=callback_id,
            selected_value=selected_value,
        )

        lark_service = get_lark_service()
        await lark_service.send_success_card(
            user_id=user_id,
            title="Selection Submitted",
            message=f"You selected: {selected_value}",
        )

    except Exception as e:
        logger.error(
            "Failed to process select async",
            callback_id=callback_id,
            error=str(e),
        )


def _build_processing_response() -> Dict[str, Any]:
    """Build processing response card."""
    card = LarkCardBuilder()
    card.set_header("Processing", "blue")
    card.add_markdown("Your action is being processed. Please wait...")
    return {
        "type": "template",
        "data": card.build(),
    }


def _build_already_processed_response() -> Dict[str, Any]:
    """Build already-processed response card."""
    card = LarkCardBuilder()
    card.set_header("Already Processed", "grey")
    card.add_markdown("This action has already been processed. Please do not repeat.")
    return {
        "type": "template",
        "data": card.build(),
    }


# ==================== 数据录入处理函数 ====================

async def _handle_menu_task_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle menu task action - show task input card."""
    from app.integrations.lark.card_forms import build_task_create_card
    from app.integrations.lark.service import get_lark_service

    project_id = action_value.get("project_id")
    project_name = action_value.get("project_name", "当前项目")

    logger.info("Showing task input card", project_id=project_id, user_id=user_id)

    lark_service = get_lark_service()
    card = build_task_create_card(project_id, project_name)
    await lark_service.send_card(user_id=user_id, card=card)

    return {"success": True, "message": "任务录入卡片已发送"}


async def _handle_menu_risk_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle menu risk action - show risk input card."""
    from app.integrations.lark.card_forms import build_risk_create_card
    from app.integrations.lark.service import get_lark_service

    project_id = action_value.get("project_id")
    project_name = action_value.get("project_name", "当前项目")

    logger.info("Showing risk input card", project_id=project_id, user_id=user_id)

    lark_service = get_lark_service()
    card = build_risk_create_card(project_id, project_name)
    await lark_service.send_card(user_id=user_id, card=card)

    return {"success": True, "message": "风险登记卡片已发送"}


async def _handle_menu_cost_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle menu cost action - show cost input card."""
    from app.integrations.lark.card_forms import build_cost_create_card
    from app.integrations.lark.service import get_lark_service

    project_id = action_value.get("project_id")
    project_name = action_value.get("project_name", "当前项目")

    logger.info("Showing cost input card", project_id=project_id, user_id=user_id)

    lark_service = get_lark_service()
    card = build_cost_create_card(project_id, project_name)
    await lark_service.send_card(user_id=user_id, card=card)

    return {"success": True, "message": "成本录入卡片已发送"}


async def _handle_menu_milestone_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle menu milestone action - show milestone input card."""
    from app.integrations.lark.card_forms import build_milestone_create_card
    from app.integrations.lark.service import get_lark_service

    project_id = action_value.get("project_id")
    project_name = action_value.get("project_name", "当前项目")

    logger.info("Showing milestone input card", project_id=project_id, user_id=user_id)

    lark_service = get_lark_service()
    card = build_milestone_create_card(project_id, project_name)
    await lark_service.send_card(user_id=user_id, card=card)

    return {"success": True, "message": "里程碑卡片已发送"}


async def _handle_create_project_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create project action."""
    # TODO: Extract form data and call ProjectService.create_project()
    logger.info("Creating project from card", user_id=user_id, action_value=action_value)
    return {"success": True, "message": "项目创建成功"}


async def _handle_create_task_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create task action."""
    # TODO: Extract form data and call TaskService.create_task()
    logger.info("Creating task from card", user_id=user_id, action_value=action_value)
    return {"success": True, "message": "任务创建成功"}


async def _handle_create_risk_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create risk action."""
    # TODO: Extract form data and call RiskService.create_risk()
    logger.info("Creating risk from card", user_id=user_id, action_value=action_value)
    return {"success": True, "message": "风险登记成功"}


async def _handle_create_cost_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create cost action."""
    # TODO: Extract form data and call CostService.create_cost()
    logger.info("Creating cost from card", user_id=user_id, action_value=action_value)
    return {"success": True, "message": "成本录入成功"}


async def _handle_create_milestone_action(
    user_id: str,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create milestone action."""
    # TODO: Extract form data and call MilestoneService.create_milestone()
    logger.info("Creating milestone from card", user_id=user_id, action_value=action_value)
    return {"success": True, "message": "里程碑创建成功"}
