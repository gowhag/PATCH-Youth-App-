import streamlit as st
from datetime import date
from openai import OpenAI
import time

st.set_page_config(page_title="Youth Support App", page_icon="🌱", layout="centered")

# ---------- OPENAI ----------
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing OPENAI_API_KEY in Streamlit secrets.")
    st.stop()

if "ASSISTANT_ID" not in st.secrets:
    st.error("Missing ASSISTANT_ID in Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------- STYLES ----------
st.markdown(
    """
    <style>
    .main {
        background-color: #F7FAFC;
    }

    .block-container {
        padding-top: 1.2rem;
        max-width: 720px;
        padding-bottom: 2rem;
    }

    .app-card {
        background: white;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
        margin-bottom: 0.9rem;
    }

    .accent-card {
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        color: white;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 0.9rem;
    }

    .small-muted {
        color: #64748B;
        font-size: 0.88rem;
    }

    .badge {
        background: #E0E7FF;
        color: #3730A3;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
    }

    .chat-shell {
        background: white;
        border-radius: 18px;
        padding: 0.8rem 0.8rem 0.2rem 0.8rem;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
        margin-bottom: 0.9rem;
    }

    .chat-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .chat-subtitle {
        color: #64748B;
        font-size: 0.88rem;
        margin-bottom: 0.9rem;
    }

    /* Makes the chat input feel cleaner */
    div[data-testid="stChatInput"] {
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SESSION STATE ----------
if "streak" not in st.session_state:
    st.session_state.streak = 3

if "points" not in st.session_state:
    st.session_state.points = 240

if "mood_log" not in st.session_state:
    st.session_state.mood_log = []

if "goals" not in st.session_state:
    st.session_state.goals = [
        {"name": "Walk 20 mins", "done": False},
        {"name": "Journal for 5 mins", "done": True},
        {"name": "Drink enough water", "done": False},
    ]

if "mock_updates" not in st.session_state:
    st.session_state.mock_updates = [
        {
            "title": "Morning check-in complete",
            "detail": "You logged a 🙂 Okay mood with 6/10 energy.",
            "tag": "Today",
        },
        {
            "title": "Goal progress",
            "detail": "1 of 3 daily goals done. Keep going!",
            "tag": "Progress",
        },
        {
            "title": "New coping tip",
            "detail": "Try 4-7-8 breathing before bedtime for better sleep.",
            "tag": "Tip",
        },
    ]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Hey! I am your AI wellbeing buddy. How are you feeling today?",
        }
    ]

if "thread_id" not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception as e:
        st.error(f"Could not create OpenAI thread: {type(e).__name__}")
        st.stop()

# ---------- HELPER ----------
def get_assistant_reply(user_prompt: str) -> str:
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_prompt,
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.secrets["ASSISTANT_ID"],
    )

    while run.status in {"queued", "in_progress", "cancelling"}:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
        )

    if run.status != "completed":
        return f"Sorry — the assistant run ended with status: {run.status}"

    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    for msg in messages.data:
        if msg.role == "assistant":
            parts = []
            for item in msg.content:
                if getattr(item, "type", None) == "text":
                    parts.append(item.text.value)
            if parts:
                return "\n\n".join(parts)

    return "Sorry — I couldn't read the assistant's reply."

# ---------- UI ----------
st.title("🌱 My Youth Space")
st.caption("A youth-focused wellbeing app experience")

home_tab, checkin_tab, goals_tab, chats_tab, resources_tab, profile_tab = st.tabs(
    ["Home", "Check-in", "Goals", "Chats", "Resources", "Profile"]
)

with home_tab:
    st.markdown(
        f"""
        <div class='accent-card'>
            <div class='small-muted' style='color: #D1D5FF;'>Welcome back 👋</div>
            <h3 style='margin: 0.3rem 0;'>You're doing great today.</h3>
            <div style='display:flex; gap:0.5rem; margin-top: 0.3rem;'>
                <span class='badge'>🔥 {st.session_state.streak}-day streak</span>
                <span class='badge'>⭐ {st.session_state.points} points</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Today at a glance")
    c1, c2 = st.columns(2)
    c1.metric("Mood trend", "Steady", "↗")
    c2.metric("Tasks done", "1 / 3", "+1")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Quick actions")
    qa1, qa2, qa3 = st.columns(3)

    if qa1.button("🧘 Breathe", key="breathe_btn"):
        st.toast("Take 4 deep breaths. You've got this.")

    if qa2.button("📝 Journal", key="journal_btn"):
        st.toast("Write one win from today.")

    if qa3.button("🎵 Calm Mix", key="calm_btn"):
        st.toast("Playing your calm playlist...")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Demo updates (fake data)")
    st.caption("Using mock content for now instead of screenshot captures.")
    for item in st.session_state.mock_updates:
        st.write(f"**{item['title']}** · {item['tag']}")
        st.caption(item["detail"])
    st.markdown("</div>", unsafe_allow_html=True)

with checkin_tab:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Daily mood check-in")

    mood = st.select_slider(
        "How are you feeling right now?",
        options=["😞 Low", "😕 Meh", "🙂 Okay", "😊 Good", "😁 Great"],
        value="🙂 Okay",
    )
    energy = st.slider("Energy level", 1, 10, 6)
    note = st.text_area(
        "Anything you'd like to note?",
        placeholder="What's on your mind today?"
    )

    if st.button("Save check-in", key="save_checkin_btn"):
        st.session_state.mood_log.append(
            {
                "date": str(date.today()),
                "mood": mood,
                "energy": energy,
                "note": note,
            }
        )
        st.session_state.points += 10
        st.success("Check-in saved. +10 points 🌟")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Recent check-ins")

    if st.session_state.mood_log:
        for entry in reversed(st.session_state.mood_log[-4:]):
            st.write(
                f"**{entry['date']}** · {entry['mood']} · Energy {entry['energy']}/10"
            )
            if entry["note"]:
                st.caption(entry["note"])
    else:
        st.caption("No check-ins yet. Save one above to see it here.")

    st.markdown("</div>", unsafe_allow_html=True)

with goals_tab:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("My daily goals")

    for i, goal in enumerate(st.session_state.goals):
        checked = st.checkbox(goal["name"], value=goal["done"], key=f"goal_{i}")
        st.session_state.goals[i]["done"] = checked

    if st.button("Update progress", key="update_progress_btn"):
        done_count = sum(1 for g in st.session_state.goals if g["done"])
        st.session_state.points = 240 + done_count * 15 + len(st.session_state.mood_log) * 10

        if done_count == len(st.session_state.goals):
            st.session_state.streak += 1
            st.balloons()
            st.success("All goals complete! Streak increased 🔥")
        else:
            st.success("Progress saved ✅")

    st.markdown("</div>", unsafe_allow_html=True)

with chats_tab:
    st.markdown("<div class='chat-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-title'>AI Chatbot</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='chat-subtitle'>Private, supportive, and youth-focused.</div>",
        unsafe_allow_html=True,
    )

    # Scrollable message area
    chat_messages_box = st.container(height=420)

    with chat_messages_box:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Input appears after messages, so it sits at the bottom of the chat card
    prompt = st.chat_input("Type a message...")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with chat_messages_box:
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        assistant_response = get_assistant_reply(prompt)
                    except Exception as e:
                        assistant_response = f"Error: {type(e).__name__}"

                    st.write(assistant_response)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_response}
        )
        st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Clear chat", key="clear_chat_btn", use_container_width=True):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "Hey! I am your AI wellbeing buddy. How are you feeling today?",
                }
            ]
            try:
                thread = client.beta.threads.create()
                st.session_state.thread_id = thread.id
            except Exception:
                pass
            st.rerun()

    with col2:
        st.button("Support mode", key="support_mode_btn", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

with resources_tab:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Support resources")
    st.markdown("- 🧠 **Coping tools:** breathing, grounding, sleep support")
    st.markdown("- 📚 **Learn:** stress basics, friendships, self-esteem")
    st.markdown("- 🚨 **Urgent help:** local helpline and emergency contacts")
    st.info("If you're in immediate danger, call your local emergency number.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("Need to talk?")
    st.write("Start a confidential chat with support when you're ready.")
    st.button("Start chat", key="start_chat_btn")
    st.markdown("</div>", unsafe_allow_html=True)

with profile_tab:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.subheader("My profile")
    st.text_input("Name", value="Alex")
    st.selectbox("Pronouns", ["they/them", "she/her", "he/him", "prefer not to say"])
    st.selectbox("Theme", ["Calm Purple", "Sunrise", "Forest", "Midnight"])
    st.toggle("Daily check-in reminders", value=True)
    st.toggle("Wellbeing tips notifications", value=True)
    st.button("Save preferences", key="save_pref_btn")
    st.markdown("</div>", unsafe_allow_html=True)
