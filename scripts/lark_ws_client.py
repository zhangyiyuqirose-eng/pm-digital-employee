#!/usr/bin/env python3
"""
PM Digital Employee - Lark WebSocket Client
飞书长连接客户端 - 接收飞书事件并转发处理

使用飞书SDK建立WebSocket长连接，无需公网HTTPS即可接收事件。
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lark_ws_client")

# 从环境变量读取配置
APP_ID = os.getenv("LARK_APP_ID", "")
APP_SECRET = os.getenv("LARK_APP_SECRET", "")

if not APP_ID or not APP_SECRET:
    logger.error("LARK_APP_ID 或 LARK_APP_SECRET 未配置")
    sys.exit(1)

logger.info(f"使用 App ID: {APP_ID}")


def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    """
    处理接收消息事件 (v2.0格式)
    
    Args:
        data: 飞书消息事件数据
    """
    try:
        # 解析消息内容
        event = data.event
        message = event.message
        sender = event.sender
        
        msg_id = message.message_id
        msg_type = message.message_type
        chat_type = message.chat_type
        chat_id = message.chat_id
        
        # 发送者信息
        sender_id = sender.sender_id
        sender_open_id = sender_id.open_id if sender_id else ""
        sender_user_id = sender_id.user_id if sender_id else ""
        
        # 解析消息内容
        content = ""
        if message.content:
            try:
                content_obj = json.loads(message.content)
                content = content_obj.get("text", "")
            except json.JSONDecodeError:
                content = message.content
        
        logger.info(
            f"收到消息: msg_id={msg_id}, type={msg_type}, "
            f"chat_type={chat_type}, sender={sender_open_id}, "
            f"content={content[:50]}..."
        )
        
        # 调用处理逻辑 - 转发到本地API处理
        asyncio.run_coroutine_threadsafe(
            process_message_async(
                message_id=msg_id,
                chat_id=chat_id,
                chat_type=chat_type,
                content=content,
                sender_open_id=sender_open_id,
                sender_user_id=sender_user_id,
            ),
            asyncio.get_event_loop()
        )
        
    except Exception as e:
        logger.error(f"处理消息事件失败: {e}", exc_info=True)


async def process_message_async(
    message_id: str,
    chat_id: str,
    chat_type: str,
    content: str,
    sender_open_id: str,
    sender_user_id: str,
) -> None:
    """
    异步处理消息 - 调用本地API或直接处理
    
    Args:
        message_id: 消息ID
        chat_id: 聊天ID
        chat_type: 聊天类型 (p2p/group)
        content: 消息内容
        sender_open_id: 发送者open_id
        sender_user_id: 发送者user_id
    """
    try:
        import httpx
        
        # 转发到本地API处理
        api_url = "http://localhost:28000/api/v1/process_message"
        
        payload = {
            "message_id": message_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "content": content,
            "sender_open_id": sender_open_id,
            "sender_user_id": sender_user_id,
        }
        
        # 内部调用处理逻辑
        # 这里直接调用消息处理服务，而不是通过HTTP
        
        logger.info(f"消息处理完成: {message_id}")
        
        # 发送回复
        await send_reply(sender_open_id, chat_id, chat_type, content)
        
    except Exception as e:
        logger.error(f"异步处理消息失败: {e}", exc_info=True)


async def send_reply(
    sender_open_id: str,
    chat_id: str,
    chat_type: str,
    user_message: str,
) -> None:
    """
    发送回复消息
    
    Args:
        sender_open_id: 发送者open_id
        chat_id: 聊天ID
        chat_type: 聊天类型
        user_message: 用户消息内容
    """
    try:
        # 创建飞书Client发送消息
        cli = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        # 生成回复内容
        reply_text = generate_reply(user_message)
        
        # 根据聊天类型选择发送方式
        if chat_type == "p2p":
            # 私聊 - 发送给用户
            req = CreateMessageReq.builder() \
                .receive_id_type("open_id") \
                .request_body(CreateMessageReqBody.builder()
                    .receive_id(sender_open_id)
                    .msg_type("text")
                    .content(json.dumps({"text": reply_text}))
                    .build()) \
                .build()
            
            resp = cli.im.v1.message.create(req)
            
        else:
            # 群聊 - 发送到群
            req = CreateMessageReq.builder() \
                .receive_id_type("chat_id") \
                .request_body(CreateMessageReqBody.builder()
                    .receive_id(chat_id)
                    .msg_type("text")
                    .content(json.dumps({"text": reply_text}))
                    .build()) \
                .build()
            
            resp = cli.im.v1.message.create(req)
        
        if resp.success():
            logger.info(f"回复发送成功")
        else:
            logger.error(f"回复发送失败: code={resp.code}, msg={resp.msg}")
            
    except Exception as e:
        logger.error(f"发送回复失败: {e}", exc_info=True)


def generate_reply(user_message: str) -> str:
    """
    生成回复内容
    
    Args:
        user_message: 用户消息
        
    Returns:
        str: 回复内容
    """
    message_lower = user_message.lower().strip()
    
    # 简单的回复逻辑（后续可接入AI）
    if "项目总览" in message_lower or "项目" in message_lower:
        return "📊 项目总览功能正在开发中，请稍后再试。"
    
    elif "周报" in message_lower:
        return "📝 周报生成功能正在开发中，请稍后再试。"
    
    elif "wbs" in message_lower:
        return "📋 WBS生成功能正在开发中，请稍后再试。"
    
    elif "风险" in message_lower:
        return "⚠️ 风险预警功能正在开发中，请稍后再试。"
    
    elif "进度" in message_lower:
        return "📈 进度更新功能正在开发中，请稍后再试。"
    
    elif "帮助" in message_lower or "help" in message_lower:
        return (
            "🤖 PM数字员工 - 项目管理智能助手\n\n"
            "支持功能:\n"
            "- 项目总览: 查看项目整体状态\n"
            "- 周报生成: 自动生成项目周报\n"
            "- WBS生成: 生成工作分解结构\n"
            "- 风险预警: 查看项目风险\n"
            "- 进度更新: 更新任务进度\n\n"
            "直接发送指令即可使用，例如: \"项目总览\""
        )
    
    else:
        return (
            "👋 您好！我是PM数字员工，您的项目管理智能助手。\n\n"
            "发送\"帮助\"查看可用功能列表。"
        )


def main():
    """启动飞书长连接客户端"""
    logger.info("=" * 50)
    logger.info("PM数字员工 - 飞书长连接客户端启动")
    logger.info("=" * 50)
    logger.info(f"App ID: {APP_ID}")
    logger.info("正在建立WebSocket连接...")
    
    # 构建事件处理器
    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1) \
        .build()
    
    # 创建WebSocket客户端
    cli = lark.ws.Client(
        APP_ID,
        APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )
    
    logger.info("WebSocket客户端已创建，开始连接...")
    logger.info("连接成功后，将自动接收飞书事件消息")
    logger.info("-" * 50)
    
    # 启动客户端 (阻塞运行)
    cli.start()


if __name__ == "__main__":
    main()