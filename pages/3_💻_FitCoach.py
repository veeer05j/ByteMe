import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="FitCoach - AI Fitness Coach",
    page_icon="💻",
    layout="centered"
)

# Groq API configuration
api_key = os.getenv("GROQ_API_KEY")

# AI Coach personality
SYSTEM_PROMPT = """
You are FitCoach, a professional and friendly AI
fitness and lifestyle coach.

Your responsibilities include:

1. FITNESS
- Create personalised workout routines.
- Help users build muscle and strength.
- Explain exercises and training techniques.
- Provide recovery and rest advice.

2. NUTRITION
- Explain calories and macronutrients.
- Suggest balanced meal ideas.
- Help users understand protein, carbs and fats.
- Encourage healthy eating habits.

3. LIFESTYLE
- Help users improve sleep and hydration.
- Encourage discipline and consistency.
- Help users develop healthy routines.
- Support personal development.

4. PERSONAL COACHING
- Understand each user's fitness goals.
- Give realistic and personalised advice.
- Ask questions when necessary.
- Break large goals into smaller steps.

PERSONALITY:
- Friendly and motivating.
- Professional but conversational.
- Easy to understand.
- Avoid generic motivational speeches.
- Never judge users based on their appearance.

SAFETY:
- You are not a medical professional.
- Never diagnose medical conditions.
- Never recommend steroids or dangerous diets.
- Do not encourage exercising through serious pain.
- Recommend professional medical advice when appropriate.
- Recommend urgent medical assistance for chest pain,
  fainting or severe breathing difficulties.

Your mission is to help users become healthier,
stronger and more consistent.
"""

# Main design
st.markdown("""
<style>
.stApp {
    background-color: #f4f7f4;
}

h1 {
    color: #176b50;
}

.stChatMessage {
    border-radius: 12px;
}

section[data-testid="stSidebar"] {
    background-color: #eaf2ec;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("💻 FitCoach")
    st.caption("Your personal fitness companion")

    st.divider()

    st.subheader("Your coach")

    st.write("🏋️ Workout planning")
    st.write("🥗 Nutrition advice")
    st.write("💤 Healthy lifestyle")
    st.write("🎯 Personal goals")

    st.divider()

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# Main heading
st.title("💻 FitCoach")

st.markdown(
    "### Your personal AI fitness and lifestyle coach"
)

st.write(
    "Let's build healthier habits, improve your fitness "
    "and work towards your goals together."
)

st.divider()

# Initialise conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! Welcome to FitCoach! 💻\n\n"
                "I'm your personal fitness and lifestyle coach. "
                "I can help you with workout plans, nutrition, "
                "muscle building and healthy habits.\n\n"
                "What's your main fitness goal?"
            )
        }
    ]

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_prompt = st.chat_input("Ask your fitness coach anything...")

if user_prompt:

    if not api_key:
        st.error("Groq API key missing. Please check your .env file.")

    else:

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Generate AI response
        with st.chat_message("assistant"):

            with st.spinner("FitCoach is thinking..."):

                try:

                    client = Groq(api_key=api_key)

                    completion = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT
                            },
                            *st.session_state.messages[-12:]
                        ],
                        max_completion_tokens=1200
                    )

                    ai_response = (
                        completion.choices[0].message.content
                    )

                    if not ai_response:
                        raise ValueError("The AI returned an empty response.")

                    st.markdown(ai_response)

                    # Save assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_response
                    })

                except Exception as error:

                    st.error(
                        f"Something went wrong: {error}"
                    )
