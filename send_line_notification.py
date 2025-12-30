#!/usr/bin/env python3
"""
發送 LINE 通知的腳本
用於 Cursor stop hook，當 Agent 終止時發送 LINE 通知
"""

import json
import sys
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import requests

# 載入 .env 檔案
load_dotenv()

# LINE Messaging API 端點
LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def get_status_message(status: str, data: Dict[str, Any]) -> str:
    """
    根據終止狀態建立對應的訊息
    
    Args:
        status: 終止狀態（如 "completed", "error", "cancelled" 等）
        data: 完整的 JSON 資料
    
    Returns:
        格式化後的訊息字串
    """
    conversation_id = data.get("conversation_id", "未知")
    model = data.get("model", "未知")
    loop_count = data.get("loop_count", 0)
    user_email = data.get("user_email", "未知")
    
    base_message = f"🔔 Cursor Agent 終止通知\n\n"
    base_message += f"狀態：{status}\n"
    base_message += f"對話 ID：{conversation_id}\n"
    base_message += f"模型：{model}\n"
    base_message += f"循環次數：{loop_count}\n"
    base_message += f"使用者：{user_email}\n"
    
    # 根據不同狀態添加額外訊息
    if status == "completed":
        message = base_message + "\n✅ Agent 已成功完成任務"
    elif status == "error":
        message = base_message + "\n❌ Agent 因錯誤而終止"
    elif status == "cancelled":
        message = base_message + "\n⚠️ Agent 已被取消"
    elif status == "timeout":
        message = base_message + "\n⏱️ Agent 因逾時而終止"
    else:
        message = base_message + f"\nℹ️ Agent 終止狀態：{status}"
    
    return message


def send_line_message(message: str, access_token: str, user_id: str) -> bool:
    """
    使用 LINE Messaging API 發送訊息
    
    Args:
        message: 要發送的訊息內容
        access_token: LINE Channel Access Token
        user_id: LINE User ID（接收者 ID）
    
    Returns:
        發送是否成功
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    try:
        response = requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"發送 LINE 通知失敗: {str(e)}", file=sys.stderr)
        if hasattr(e.response, 'text'):
            print(f"回應內容: {e.response.text}", file=sys.stderr)
        return False


def main():
    """主函數：讀取 JSON 輸入，發送 LINE 通知"""
    try:
        # 從 stdin 讀取 UTF-8 編碼的 JSON 資料
        input_data = sys.stdin.buffer.read().decode('utf-8')
        
        # 解析 JSON
        try:
            data: Dict[str, Any] = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤: {str(e)}", file=sys.stderr)
            sys.exit(1)
        
        # 取得終止狀態
        status = data.get("status", "unknown")
        
        # 取得 LINE 設定
        access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        user_id = os.getenv("LINE_USER_ID")
        
        # 檢查必要的環境變數
        if not access_token:
            print("錯誤: LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定", file=sys.stderr)
            sys.exit(1)
        
        if not user_id:
            print("錯誤: LINE_USER_ID 環境變數未設定", file=sys.stderr)
            sys.exit(1)
        
        # 建立訊息
        message = get_status_message(status, data)
        
        # 發送 LINE 通知
        success = send_line_message(message, access_token, user_id)
        
        if success:
            print("LINE 通知已成功發送", file=sys.stderr)
            sys.exit(0)
        else:
            print("LINE 通知發送失敗", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"發生未預期的錯誤: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()






