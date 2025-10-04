import streamlit as st
import requests
import json
import time
import random

# 頁面配置
st.set_page_config(
    page_title="任務拆分器",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 應用標題和描述
st.title("拖延症助手 🤝🏼")
st.markdown("### 任務碎片化，拯救拖延的你！")

# 初始化 session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'show_celebration' not in st.session_state:
    st.session_state.show_celebration = False
if 'task_input' not in st.session_state:
    st.session_state.task_input = ""
if 'custom_task_text' not in st.session_state:
    st.session_state.custom_task_text = ""

# 從 Streamlit secrets 獲取 API 密鑰
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
model = "tngtech/deepseek-r1t2-chimera:free"

# 激勵語句
motivation_phrases = [
    "萬事起頭難，讓我們從一小步開始！",
    "完成一個小任務，就是向成功邁進一步！",
    "不必一次做完所有事，只需開始第一步！",
    "每個偉大的成就都始於一個小小的決定！",
    "你比你想像的更有能力完成這些任務！",
    "慢慢來，但不要停下來！",
    "完成一個任務，就獎勵自己一下！"
]

# 任務模板 (預設使用)
task_templates = {
    "收拾房間": [
        "🎯 把地上的衣物撿起來，分類為要洗和乾淨的 - 這一步很簡單，只需要5分鐘！",
        "📚 將書桌上的雜物歸位 - 你會發現空間變整潔了！",
        "🛏️ 整理床鋪，把被子疊好 - 完成後床看起來會很舒服",
        "🧹 用抹布擦拭桌面和傢俱表面 - 灰塵不見了，心情也變好",
        "🗑️ 把垃圾收集起來丟掉 - 很快就能完成，加油！",
        "🧽 用吸塵器或掃把清潔地板 - 最後一步了，馬上就能完成！",
        "🌬️ 打開窗戶讓空氣流通 - 享受清新的空氣，你做得很好！"
    ],
    "準備考試": [
        "📖 整理所有需要複習的科目和章節 - 先理清思路，這很重要！",
        "📅 制定一個為期一週的複習計劃表 - 有計劃就不會慌亂",
        "✏️ 準備好筆記本、螢光筆等學習用品 - 準備好工具讓學習更順利",
        "🧠 複習第一個重要章節 - 從最簡單的開始，建立信心",
        "📝 做相關章節的練習題 - 實踐是檢驗真理的唯一標準",
        "📋 整理易錯題目和重點筆記 - 總結經驗，避免再犯",
        "☕ 休息10分鐘，放鬆眼睛和大腦 - 適當休息很重要",
        "🚀 繼續複習下一個章節 - 你已經進入狀態了，繼續加油！"
    ],
    "開始健身": [
        "👕 準備舒適的運動服裝和鞋子 - 好的裝備讓運動更愉快",
        "📱 選擇一個適合初學者的健身影片或應用程式 - 找到適合自己的方式",
        "🧘 準備瑜伽墊和一瓶水 - 做好準備工作",
        "🔥 進行5分鐘的熱身運動 - 讓身體準備好，避免受傷",
        "💪 完成15分鐘的主要訓練 - 堅持就是勝利！",
        "🔄 進行5分鐘的緩和伸展 - 放鬆肌肉，感覺很棒",
        "📝 記錄今天的運動成果和感受 - 為自己的努力點讚！"
    ],
    "整理檔案": [
        "📁 在桌面創建一個「待整理」資料夾 - 先把所有東西集中起來",
        "📄 將桌面上所有檔案移動到待整理資料夾 - 桌面變乾淨了！",
        "🗂️ 按照專案或類別創建新的資料夾 - 有條理地分類",
        "📂 將檔案分類到對應的資料夾中 - 一步步來，不要急",
        "🗑️ 刪除不需要的舊檔案和重複檔案 - 釋放空間，心情也輕鬆",
        "🏷️ 為重要檔案重新命名，方便查找 - 以後找檔案更容易了",
        "☁️ 備份重要檔案到雲端或外接硬碟 - 最後一步，確保安全"
    ]
}

# 使用 AI 拆分任務的函數
def split_task_with_ai(task, api_key, model):
    """使用 OpenRouter API 拆分任務"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://task-splitter.streamlit.app',
            'X-Title': 'Task Splitter App'
        }
        
        # 改進的提示詞 - 避免重複步驟，要求連續性
        system_prompt = """你是一個專門幫助懶人和容易拖延的人的任務拆分助手，特別針對INTP人格類型設計。INTP喜歡邏輯和系統性思考，但容易因完美主義或過度分析而拖延，因此步驟需從最簡單的物理行動開始，逐步建立動能。

請遵循以下指示：

1. 將用戶的大任務拆分為5-9個具體、可執行的小步驟，每一步應盡可能微小（理想在5分鐘內完成）。
2. 步驟之間必須有邏輯順序和連續性，後一步驟應直接建立在前一步驟的基礎上，以符合INTP的系統思考偏好。
3. 避免重複的步驟或提供多種選擇（例如：不要同時建議「看視頻學習」和「讀書學習」），減少決策疲勞。
4. 每個步驟應該非常簡單和具體，適合容易拖延的人。
5. 在每個步驟中加入只有一個表情符號，言語增加趣味性。
6. 除了專有名詞外，使用繁體中文回答，即使用戶使用英文輸入。
7. 讓每個步驟看起來都很容易完成，降低開始的門檻，並強調「只需一小步」的心態。
8. 使用親切、鼓勵的語氣，像是朋友在鼓勵對方一樣，並在鼓勵話語中強調每個小完成的成就感（例如「你已經開始了，這太棒了！」）。
9. 每個步驟盡量不超過15個字，每個小步驟都是具體行動，不要只有鼓勵的話語。
10. 針對INTP類型，步驟應注重邏輯性和系統性，例如從「定義問題」到「執行小實驗」，以激發他們的內在動機，但不用在步驟中提及人格類型。

請按照以下格式返回：

[表情符號] 第一步驟描述 (粗體字) - 鼓勵的話語
[表情符號] 第二步驟描述 (粗體字) - 鼓勵的話語
...

例如對於「學習微積分」：
📚 找到一本適合初學者的微積分教材 - 選擇合適的教材是成功的第一步，這很簡單吧！
🎯 學習極限的基本概念 - 這是微積分的基礎，慢慢來，你一定能理解！
📝 練習導數的基本計算 - 多做練習會越來越熟練，從一個小題開始就好！
🔄 學習積分的概念和計算 - 你已經掌握導數了，積分也不難，繼續前進！
✅ 做綜合練習題鞏固知識 - 把學過的知識融會貫通，每一步都在累積成就感！
🚀 嘗試解決一些實際應用問題 - 看看微積分在現實中的應用，很有趣吧，你做得很好！
"""
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"請將以下任務拆分為具體的小步驟：{task}"
                }
            ],
            "max_tokens": 1500
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # 處理 AI 回應，提取步驟
            steps = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                # 提取有編號的步驟 (1., 2., 3. 等)
                if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                    # 移除編號和點
                    clean_line = line.split('.', 1)[1].strip()
                    if clean_line and len(clean_line) > 5:
                        steps.append(clean_line)
                # 也處理其他格式的步驟
                elif line and len(line) > 10 and not line.startswith(('步驟', '階段', '以下是', '任務', '請將', '拆分')):
                    # 檢查是否包含表情符號或看起來像步驟
                    if any(marker in line for marker in ['-', '—', '•', '→', '>>']) or any(emoji in line for emoji in ['🎯', '📚', '🛏️', '🧹', '🗑️', '🧽', '🌬️', '📖', '📅', '✏️', '🧠', '📝', '📋', '☕', '🚀', '👕', '📱', '🧘', '🔥', '💪', '🔄', '📁', '📄', '🗂️', '📂', '🏷️', '☁️']):
                        steps.append(line)
            
            # 如果步驟太少，添加一些預設步驟
            if len(steps) < 4:
                st.warning("AI 生成的步驟較少，已補充一些預設步驟")
                base_steps = [
                    "🎯 開始第一步 - 萬事起頭難，但開始了就成功一半！",
                    "📝 準備必要的工具和材料 - 好的準備是成功的一半",
                    "🔄 按順序執行任務 - 一步步來，不要著急",
                    "✅ 檢查完成情況 - 看看自己的成果，很棒吧！",
                    "🎉 慶祝任務完成 - 你做到了！獎勵自己一下"
                ]
                # 合併 AI 生成的步驟和預設步驟
                steps = steps + base_steps[len(steps):]
            
            # 確保至少有5個步驟
            while len(steps) < 5:
                steps.append(f"步驟 {len(steps)+1} - 繼續保持，你做得很好！")
            
            return steps[:10]  # 限制最多10個步驟
            
        else:
            error_msg = f"API 請求失敗: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', '未知錯誤')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)
            
    except Exception as e:
        raise Exception(f"AI 拆分失敗: {str(e)}")

# 使用模板拆分任務的函數
def split_task_with_template(task):
    """使用預設模板拆分任務"""
    for key, steps in task_templates.items():
        if key in task:
            return steps
    # 通用模板 - 使用鼓勵性語言
    return [
        "🎯 分析任務的主要組成部分 - 先了解要做什麼，這很簡單！",
        "📋 列出完成任務所需的材料和工具 - 準備好就成功一半了",
        "⏰ 設定一個明確的開始時間 - 現在就是最好的開始時機",
        "🚀 完成第一步準備工作 - 開始了就會發現沒那麼難",
        "📝 按順序執行任務的各個部分 - 一步步來，你可以的！",
        "✅ 檢查完成品質並做最後調整 - 看看自己的成果，很棒吧",
        "🎉 慶祝任務完成！ - 你做到了！給自己一個讚"
    ]

# 處理任務拆分的函數
def handle_task_splitting(task_input, use_template=False):
    """處理任務拆分的統一函數"""
    if not task_input:
        st.error("請輸入一個任務！")
        return
    
    with st.spinner("正在為您拆分任務中..." if use_template else "AI 正在為您拆分任務中..."):
        try:
            if use_template or not api_key:
                # 使用模板拆分
                steps = split_task_with_template(task_input)
                st.success("任務拆分完成！")
            else:
                # 使用 AI 拆分
                steps = split_task_with_ai(task_input, api_key, model)
                st.success("AI 任務拆分完成！")
            
            # 保存任務到 session state
            st.session_state.tasks = [
                {"text": step, "completed": False} 
                for step in steps
            ]
            st.session_state.progress = 0
            st.session_state.show_celebration = False
            
        except Exception as e:
            st.error(f"任務拆分失敗: {str(e)}")
            # 失敗時使用模板
            steps = split_task_with_template(task_input)
            st.session_state.tasks = [
                {"text": step, "completed": False} 
                for step in steps
            ]
            st.info("已使用預設模板為您拆分任務")

# 重置函數
def reset_app():
    """重置應用狀態"""
    st.session_state.tasks = []
    st.session_state.progress = 0
    st.session_state.show_celebration = False
    st.session_state.task_input = ""
    st.session_state.custom_task_text = ""

# 添加自定義 CSS - 修復按鈕格式並稍微增加字體
st.markdown("""
<style>
/* 整體字體稍微增大 */
html, body, [class*="css"] {
    font-size: 14px !important;
}

/* 標題字體 */
h1 {
    font-size: 1.8rem !important;
}
h2 {
    font-size: 1.4rem !important;
}
h3 {
    font-size: 1.2rem !important;
}

/* 複選框字體和間距 */
.stCheckbox > label {
    font-size: 0.9rem !important;
    line-height: 1.3 !important;
    padding: 3px 0 !important;
    margin: 0 !important;
}

/* 左側按鈕保持原有樣式 */
.stButton button:not([kind="secondary"]) {
    font-size: 0.9rem !important;
    padding: 8px 16px !important;
    border-radius: 10px !important;
    background: linear-gradient(135deg, #6a89cc, #4a69bd) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(106, 137, 204, 0.3) !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton button:not([kind="secondary"]):hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(106, 137, 204, 0.4) !important;
    background: linear-gradient(135deg, #5a79bc, #3a59ad) !important;
}

/* 文本輸入字體 */
.stTextArea textarea, .stTextInput input {
    font-size: 1.1rem !important;
}

/* 進度條高度 */
.stProgress > div > div > div {
    height: 8px !important;
}

/* 任務項目的垂直間距 */
.row-widget.stCheckbox {
    padding: 1px 0 !important;
    margin: 0 !important;
    min-height: 24px !important;
}
</style>
""", unsafe_allow_html=True)

# 創建三列布局 - 添加間隔列
col1, spacer, col2 = st.columns([1, 0.05, 2])  # 中間添加一個很窄的間隔列

# 左側 - 輸入區域
with col1:
    st.subheader("📝 輸入任務")
    
    # 任務輸入
    task_input = st.text_area(
        "描述您想要完成的任務",
        placeholder="例如：我想學習某種技能...",
        height=90,
        value=st.session_state.task_input,
        key="main_task_input",
        label_visibility="collapsed"
    )
    
    # 更新 session state
    if task_input != st.session_state.task_input:
        st.session_state.task_input = task_input

    # 操作按鈕 - 現在在範例任務上方
    action_cols = st.columns(2)

    with action_cols[0]:
        # AI 拆分按鈕 (僅在有 API 密鑰時啟用)
        if api_key:
            if st.button("🚀 AI 拆分任務", use_container_width=True, type="primary", key="ai_split_button"):
                handle_task_splitting(st.session_state.task_input, use_template=False)
        else:
            st.button("🚀 AI 拆分任務", use_container_width=True, disabled=True, 
                     help="需要設置 OpenRouter API 密鑰才能使用 AI 功能")

    with action_cols[1]:
        # 重置按鈕
        if st.button("🔄 重置", use_container_width=True, key="reset_button"):
            reset_app()
            st.rerun()

    # 範例任務按鈕 - 現在在操作按鈕下方
    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
    st.markdown("**快速範例:**")
    example_cols = st.columns(2)
        
    example_tasks = {
        "🧹 收拾房間": "收拾房間",
        "📚 準備考試": "準備考試", 
        "💪 開始健身": "開始健身",
        "💻 整理檔案": "整理檔案"
    }

    # 第一行按鈕
    with example_cols[0]:
        if st.button("🧹 收拾房間", use_container_width=True, key="example_0"):
            st.session_state.task_input = example_tasks["🧹 收拾房間"]
            handle_task_splitting(example_tasks["🧹 收拾房間"], use_template=True)
        
        if st.button("💪 開始健身", use_container_width=True, key="example_2"):
            st.session_state.task_input = example_tasks["💪 開始健身"]
            handle_task_splitting(example_tasks["💪 開始健身"], use_template=True)

    # 第二行按鈕
    with example_cols[1]:
        if st.button("📚 準備考試", use_container_width=True, key="example_1"):
            st.session_state.task_input = example_tasks["📚 準備考試"]
            handle_task_splitting(example_tasks["📚 準備考試"], use_template=True)
        
        if st.button("💻 整理檔案", use_container_width=True, key="example_3"):
            st.session_state.task_input = example_tasks["💻 整理檔案"]
            handle_task_splitting(example_tasks["💻 整理檔案"], use_template=True)

    # API 狀態提示
    if not api_key:
        st.info("💡 提示: 要使用 AI 拆分功能，請在 Streamlit 的 Secrets 中設置 OPENROUTER_API_KEY")

# 右側 - 輸出區域
with col2:
    # 任務列表和進度
    if st.session_state.tasks:
        st.subheader("📋 任務步驟")
        
        # 進度條
        completed_tasks = sum(1 for task in st.session_state.tasks if task["completed"])
        total_tasks = len(st.session_state.tasks)
        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        st.progress(progress / 100)
        st.markdown(f"**進度: {completed_tasks}/{total_tasks} 完成 ({progress:.0f}%)**")
        
        # 任務列表 - 使用更緊湊的佈局
        st.markdown("### 您的任務:")
        
        # 顯示所有任務
        for i, task in enumerate(st.session_state.tasks):
            # 複選框
            completed = st.checkbox(
                task["text"],
                value=task["completed"],
                key=f"task_{i}"
            )
            
            if completed != task["completed"]:
                st.session_state.tasks[i]["completed"] = completed
                st.rerun()
        
        # 檢查是否所有任務都完成
        if all(task["completed"] for task in st.session_state.tasks) and total_tasks > 0:
            st.session_state.show_celebration = True

        # 慶祝訊息
        if st.session_state.get('show_celebration', False):
            st.balloons()
            st.success("🎉 恭喜！您已完成所有任務！真是太棒了！休息一下，獎勵自己吧！")

        # 激勵語句 (隨機顯示)
        if st.session_state.tasks:
            motivation = random.choice(motivation_phrases)
            st.info(f"💡 {motivation}")

# 底部資訊
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        <p>小步前進，也能到達遠方 | 智能任務拆分助手</p>
    </div>
    """,
    unsafe_allow_html=True
)