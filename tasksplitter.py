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
if 'selected_mbti' not in st.session_state:
    st.session_state.selected_mbti = "INTP"  # 默认值

# 从 Streamlit secrets 获取 API 密钥
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
model = "tngtech/deepseek-r1t2-chimera:free"

# 激励语句
motivation_phrases = [
    "萬事起頭難，讓我們從一小步開始！",
    "完成一個小任務，就是向成功邁進一步！",
    "不必一次做完所有事，只需開始第一步！",
    "每個偉大的成就都始於一個小小的決定！",
    "你比你想像的更有能力完成這些任務！",
    "慢慢來，但不要停下來！",
    "完成一個任務，就獎勵自己一下！"
]

# MBTI 提示词配置
mbti_prompts = {
    "INFJ": """你是一個專門幫助懶人和容易拖延的人的任務拆分助手，特別針對INFJ人格類型設計。INFJ重視意義、和諧與整體願景，但容易因追求完美或過度考慮他人而拖延，因此步驟需從情感連結和意義出發，逐步建立完成動力。

請遵循以下指示：

1. 將用戶的大任務拆分為5-9個具體、可執行的小步驟，每一步應盡可能微小且充滿意義。
2. 步驟之間必須有情感連貫性，後一步驟應能讓用戶感受到進展的意義和價值。
3. 避免過於機械化的步驟，強調每個行動的內在價值和對整體的貢獻。
4. 每個步驟應該簡單具體，但需包含情感連結或意義提示。
5. 在每個步驟中加入只有一個表情符號，增加情感共鳴。
6. 除了專有名詞外，使用繁體中文回答(香港繁體中文)，即使用戶使用英文輸入。
7. 讓每個步驟看起來都很溫暖且容易完成，強調「每一小步都有意義」。
8. 使用溫暖、共情的語氣，強調每個步驟如何貢獻於更大目標。
9. 每個步驟盡量不超過15個字，但可適當放寬以容納意義描述。
10. 針對INFJ類型，步驟應注重情感連結和整體願景，例如從「設定意圖」到「分享成果」，但不用在步驟中提及人格類型。

請按照以下格式返回：

[表情符號] 第一步驟描述 (粗體字) - 鼓勵的話語
[表情符號] 第二步驟描述 (粗體字) - 鼓勵的話語
...

例如對於「學習微積分」：
💭 靜心思考學習微積分的意義 - 找到內在動機能讓學習更有溫度！
📖 選擇一本有溫暖範例的教材 - 好的開始能讓學習旅程更愉快！
🎯 設定一個小而美的學習目標 - 每個小目標都是通往夢想的階梯！
✍️ 用喜歡的筆記本寫下第一個概念 - 親手記錄能讓知識更有生命力！
🔄 將概念與生活實例連結 - 發現知識的實用意義會讓你更投入！
🌟 分享一個學到的小知識 - 與他人分享能讓學習變得更有價值！""",

    "INTP": """你是一個專門幫助懶人和容易拖延的人的任務拆分助手，特別針對INTP人格類型設計。INTP喜歡邏輯和系統性思考，但容易因完美主義或過度分析而拖延，因此步驟需從最簡單的物理行動開始，逐步建立動能。

請遵循以下指示：

1. 將用戶的大任務拆分為5-9個具體、可執行的小步驟，每一步應盡可能微小（理想在5分鐘內完成）。
2. 步驟之間必須有邏輯順序和連續性，後一步驟應直接建立在前一步驟的基礎上，以符合INTP的系統思考偏好。
3. 避免重複的步驟或提供多種選擇（例如：不要同時建議「看視頻學習」和「讀書學習」），減少決策疲勞。
4. 每個步驟應該非常簡單和具體，不需要整句只有鼓勵但沒有行動的步驟。
5. 在每個步驟中加入只有一個表情符號，言語增加趣味性。
6. 除了專有名詞外，使用繁體中文回答(香港繁體中文)，即使用戶使用英文輸入。
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
🚀 嘗試解決一些實際應用問題 - 看看微積分在現實中的應用，很有趣吧，你做得很好！""",

    "ENFP": """你是一個專門幫助懶人和容易拖延的人的任務拆分助手，特別針對ENFP人格類型設計。ENFP充滿熱情和創意，但容易因興趣廣泛或厭倦常規而拖延，因此步驟需從有趣和新鮮的體驗開始，保持動力。

請遵循以下指示：

1. 將用戶的大任務拆分為5-9個具體、可執行的小步驟，每一步應包含創意或變化。
2. 步驟之間要有趣味性和多樣性，避免單調重複的模式。
3. 強調每個步驟的新鮮感和創造性，讓任務變得有趣。
4. 每個步驟應該簡單但富有想像空間。
5. 在每個步驟中加入只有一個表情符號，增加活潑感。
6. 除了專有名詞外，使用繁體中文回答(香港繁體中文)，即使用戶使用英文輸入。
7. 讓每個步驟看起來都像一個小冒險，充滿可能性。
8. 使用熱情、鼓舞的語氣，強調探索和發現的樂趣。
9. 每個步驟盡量不超過15個字，但要保持生動有趣。
10. 針對ENFP類型，步驟應注重創意探索和多樣體驗，但不用在步驟中提及人格類型。

請按照以下格式返回：

[表情符號] 第一步驟描述 (粗體字) - 鼓勵的話語
[表情符號] 第二步驟描述 (粗體字) - 鼓勵的話語
...

例如對於「學習微積分」：
🎨 用彩色筆畫出數學概念圖 - 讓學習變成有趣的藝術創作！
🔍 探索微積分在現實中的奇妙應用 - 發現數學的魔法世界！
📱 找個有趣的數學學習APP試玩 - 用科技讓學習更好玩！
🎯 設定一個有趣的學習挑戰 - 把學習變成闖關遊戲！
🌟 與朋友分享一個有趣的數學發現 - 讓學習成為社交樂趣！
🚀 嘗試用微積分解決一個生活問題 - 體驗數學的實用魔力！"""
}

# 任务模板 (预设使用)
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
        "🏷️ 為重要檔案重新命名，方便查找 - 以後找檔案更容易",
        "☁️ 備份重要檔案到雲端或外接硬碟 - 最後一步，確保安全"
    ]
}

# 使用 AI 拆分任务的函数
def split_task_with_ai(task, api_key, model, mbti_type):
    """使用 OpenRouter API 拆分任务"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://task-splitter.streamlit.app',
            'X-Title': 'Task Splitter App'
        }
        
        # 根据选择的 MBTI 类型使用对应的提示词
        system_prompt = mbti_prompts.get(mbti_type, mbti_prompts["INFJ"])
        
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
            
            # 处理 AI 回应，提取步骤
            steps = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                # 提取有编号的步骤 (1., 2., 3. 等)
                if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                    # 移除编号和点
                    clean_line = line.split('.', 1)[1].strip()
                    if clean_line and len(clean_line) > 5:
                        steps.append(clean_line)
                # 也处理其他格式的步骤
                elif line and len(line) > 10 and not line.startswith(('步驟', '階段', '以下是', '任務', '請將', '拆分')):
                    # 检查是否包含表情符号或看起来像步骤
                    if any(marker in line for marker in ['-', '—', '•', '→', '>>']) or any(emoji in line for emoji in ['🎯', '📚', '🛏️', '🧹', '🗑️', '🧽', '🌬️', '📖', '📅', '✏️', '🧠', '📝', '📋', '☕', '🚀', '👕', '📱', '🧘', '🔥', '💪', '🔄', '📁', '📄', '🗂️', '📂', '🏷️', '☁️']):
                        steps.append(line)
            
            # 如果步骤太少，添加一些预设步骤
            if len(steps) < 4:
                st.warning("AI 生成的步驟較少，已補充一些預設步驟")
                base_steps = [
                    "🎯 開始第一步 - 萬事起頭難，但開始了就成功一半！",
                    "📝 準備必要的工具和材料 - 好的準備是成功的一半",
                    "🔄 按順序執行任務 - 一步步來，不要著急",
                    "✅ 檢查完成情況 - 看看自己的成果，很棒吧！",
                    "🎉 慶祝任務完成 - 你做到了！獎勵自己一下"
                ]
                # 合并 AI 生成的步骤和预设步骤
                steps = steps + base_steps[len(steps):]
            
            # 确保至少有5个步骤
            while len(steps) < 5:
                steps.append(f"步驟 {len(steps)+1} - 繼續保持，你做得很好！")
            
            return steps[:10]  # 限制最多10个步骤
            
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

# 使用模板拆分任务的函数
def split_task_with_template(task):
    """使用预设模板拆分任务"""
    for key, steps in task_templates.items():
        if key in task:
            return steps
    # 通用模板 - 使用鼓励性语言
    return [
        "🎯 分析任務的主要組成部分 - 先了解要做什麼，這很簡單！",
        "📋 列出完成任務所需的材料和工具 - 準備好就成功一半了",
        "⏰ 設定一個明確的開始時間 - 現在就是最好的開始時機",
        "🚀 完成第一步準備工作 - 開始了就會發現沒那麼難",
        "📝 按順序執行任務的各個部分 - 一步步來，你可以的！",
        "✅ 檢查完成品質並做最後調整 - 看看自己的成果，很棒吧",
        "🎉 慶祝任務完成！ - 你做到了！給自己一個讚"
    ]

# 处理任务拆分的函数
def handle_task_splitting(task_input, use_template=False):
    """处理任务拆分的统一函数"""
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
                # 使用 AI 拆分，传入当前选择的 MBTI 类型
                steps = split_task_with_ai(task_input, api_key, model, st.session_state.selected_mbti)
                st.success(f"AI 任務拆分完成！(使用 {st.session_state.selected_mbti} 模式)")
            
            # 保存任务到 session state
            st.session_state.tasks = [
                {"text": step, "completed": False} 
                for step in steps
            ]
            st.session_state.progress = 0
            st.session_state.show_celebration = False
            
        except Exception as e:
            st.error(f"任務拆分失敗: {str(e)}")
            # 失败时使用模板
            steps = split_task_with_template(task_input)
            st.session_state.tasks = [
                {"text": step, "completed": False} 
                for step in steps
            ]
            st.info("已使用預設模板為您拆分任務")

# 重置函数
def reset_app():
    """重置应用状态"""
    st.session_state.tasks = []
    st.session_state.progress = 0
    st.session_state.show_celebration = False
    st.session_state.task_input = ""
    st.session_state.custom_task_text = ""

# 添加自定义 CSS - 修复按钮格式并稍微增加字体
st.markdown("""
<style>
/* 整体字体稍微增大 */
html, body, [class*="css"] {
    font-size: 14px !important;
}

/* 标题字体 */
h1 {
    font-size: 1.8rem !important;
}
h2 {
    font-size: 1.4rem !important;
}
h3 {
    font-size: 1.2rem !important;
}

/* 复选框字体和间距 */
.stCheckbox > label {
    font-size: 0.9rem !important;
    line-height: 1.3 !important;
    padding: 3px 0 !important;
    margin: 0 !important;
}

/* 左侧按钮保持原有样式 */
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

/* 文本输入字体 */
.stTextArea textarea, .stTextInput input {
    font-size: 1.1rem !important;
}

/* 进度条高度 */
.stProgress > div > div > div {
    height: 8px !important;
}

/* 任务项目的垂直间距 */
.row-widget.stCheckbox {
    padding: 1px 0 !important;
    margin: 0 !important;
    min-height: 24px !important;
}
</style>
""", unsafe_allow_html=True)

# 创建三列布局 - 添加间隔列
col1, spacer, col2 = st.columns([1, 0.05, 2])  # 中间添加一个很窄的间隔列

# 左侧 - 输入区域
with col1:
    st.subheader("📝 輸入任務")
    
    # MBTI 类型选择下拉菜单
    mbti_options = ["INFJ", "INTP", "ENFP"]  # 可以继续添加更多类型
    selected_mbti = st.selectbox(
        "選擇您的 MBTI 人格類型",
        options=mbti_options,
        index=mbti_options.index(st.session_state.selected_mbti) if st.session_state.selected_mbti in mbti_options else 0,
        key="mbti_select"
    )
    st.session_state.selected_mbti = selected_mbti
    
    # 显示当前选择的 MBTI 类型描述
    mbti_descriptions = {
        "INFJ": "🤝 理想主義者 - 重視意義與和諧，適合情感連結的步驟",
        "INTP": "🧠 邏輯學家 - 喜歡系統思考，適合邏輯清晰的步驟", 
        "ENFP": "🎉 激勵者 - 充滿熱情創意，適合有趣多樣的步驟"
    }
    st.caption(mbti_descriptions.get(selected_mbti, ""))
    
    # 任务输入 - 使用 key 参数来确保实时同步
    task_input = st.text_area(
        "描述您想要完成的任務",
        placeholder="例如：我想學習某種技能...",
        height=90,
        value=st.session_state.task_input,
        key="task_input_widget",  # 添加 key 来确保实时同步
        label_visibility="collapsed"
    )
    
    # 实时更新 session state - 这行很重要！
    st.session_state.task_input = task_input

    # 操作按钮 - 现在在范例任务上方
    action_cols = st.columns(2)

    with action_cols[0]:
        # AI 拆分按钮 (仅在有 API 密钥时启用)
        if api_key:
            if st.button("🚀 AI 拆分任務", use_container_width=True, type="primary", key="ai_split_button"):
                # 确保使用最新的输入内容
                handle_task_splitting(st.session_state.task_input, use_template=False)
        else:
            st.button("🚀 AI 拆分任務", use_container_width=True, disabled=True, 
                     help="需要設置 OpenRouter API 密鑰才能使用 AI 功能")

    with action_cols[1]:
        # 重置按钮
        if st.button("🔄 重置", use_container_width=True, key="reset_button"):
            reset_app()
            st.rerun()

    # 范例任务按钮 - 现在在操作按钮下方
    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
    st.markdown("**快速範例:**")
    example_cols = st.columns(2)
        
    example_tasks = {
        "🧹 收拾房間": "收拾房間",
        "📚 準備考試": "準備考試", 
        "💪 開始健身": "開始健身",
        "💻 整理檔案": "整理檔案"
    }

    # 第一行按钮
    with example_cols[0]:
        if st.button("🧹 收拾房間", use_container_width=True, key="example_0"):
            st.session_state.task_input = example_tasks["🧹 收拾房間"]
            handle_task_splitting(example_tasks["🧹 收拾房間"], use_template=True)
        
        if st.button("💪 開始健身", use_container_width=True, key="example_2"):
            st.session_state.task_input = example_tasks["💪 開始健身"]
            handle_task_splitting(example_tasks["💪 開始健身"], use_template=True)

    # 第二行按钮
    with example_cols[1]:
        if st.button("📚 準備考試", use_container_width=True, key="example_1"):
            st.session_state.task_input = example_tasks["📚 準備考試"]
            handle_task_splitting(example_tasks["📚 準備考試"], use_template=True)
        
        if st.button("💻 整理檔案", use_container_width=True, key="example_3"):
            st.session_state.task_input = example_tasks["💻 整理檔案"]
            handle_task_splitting(example_tasks["💻 整理檔案"], use_template=True)

    # API 状态提示
    if not api_key:
        st.info("💡 提示: 要使用 AI 拆分功能，請在 Streamlit 的 Secrets 中設置 OPENROUTER_API_KEY")

# 右侧 - 输出区域
with col2:
    # 任务列表和进度
    if st.session_state.tasks:
        st.subheader("📋 任務步驟")
        
        # 显示当前使用的 MBTI 模式
        if api_key and st.session_state.tasks:
            st.caption(f"當前使用: {st.session_state.selected_mbti} 專屬模式")
        
        # 进度条
        completed_tasks = sum(1 for task in st.session_state.tasks if task["completed"])
        total_tasks = len(st.session_state.tasks)
        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        st.progress(progress / 100)
        st.markdown(f"**進度: {completed_tasks}/{total_tasks} 完成 ({progress:.0f}%)**")
        
        # 任务列表 - 使用更紧凑的布局
        st.markdown("### 您的任務:")
        
        # 显示所有任务
        for i, task in enumerate(st.session_state.tasks):
            # 复选框
            completed = st.checkbox(
                task["text"],
                value=task["completed"],
                key=f"task_{i}"
            )
            
            if completed != task["completed"]:
                st.session_state.tasks[i]["completed"] = completed
                st.rerun()
        
        # 检查是否所有任务都完成
        if all(task["completed"] for task in st.session_state.tasks) and total_tasks > 0:
            st.session_state.show_celebration = True

        # 庆祝讯息
        if st.session_state.get('show_celebration', False):
            st.balloons()
            st.success("🎉 恭喜！您已完成所有任務！真是太棒了！休息一下，獎勵自己吧！")

        # 激励语句 (随机显示)
        if st.session_state.tasks:
            motivation = random.choice(motivation_phrases)
            st.info(f"💡 {motivation}")

# 底部信息
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        <p>小步前進，也能到達遠方 | 智能任務拆分助手 | MBTI 專屬模式</p>
    </div>
    """,
    unsafe_allow_html=True
)