# ✒️ ESL Writing Mentor: AI-Powered IELTS Evaluator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.42.0-FF4B4B?logo=streamlit&logoColor=white)
![Hugging Face](https://img.shields.io/badge/HuggingFace-Inference_API-F58220?logo=huggingface&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Qwen_2.5_72B-purple)

**Live Demo:** [Click here to try the ESL Writing Mentor](https://esl-writing-mentor-kjrydncqyrvldqwnvvmqbm.streamlit.app/)

## 📌 Overview
ESL Writing Mentor is an end-to-end NLP web application designed to simulate a rigorous IELTS Examiner and an ESL Writing Coach. Built at the intersection of English Language Teaching (ELT) methodologies and Natural Language Processing (NLP), this tool provides ESL students with real-time, highly granular feedback on their essays.

Unlike standard chatbots, this application utilizes **Dual-Stream Prompting** and **Regex Parsing** to deliver feedback in two distinct layers:
1. **Inline Highlights:** Pinpoints exact errors in the text with interactive tooltips (Spelling, Grammar, Vocabulary, Style).
2. **Comprehensive Report:** Generates a detailed breakdown of Task Achievement, Coherence, Lexical Resource, and Grammatical Range based on IELTS assessment criteria.

## ✨ Key Features
* **Custom AI Personas:** Choose the feedback tone (Supportive, Professional, Strict & Detailed).
* **Two Distinct Modes:**
  * **Fast Analysis:** Instant evaluation of pasted texts or uploaded `.docx` / `.txt` files.
  * **Draft Creator:** A guided 3-step pipeline (Outline -> Draft 1 -> Final Draft) where the AI acts as a coach in the intermediate steps before acting as an examiner for the final evaluation.
* **Smart UI Limits:** Client-side and server-side word count validation (50-500 words) and strict file size limits (2MB via `config.toml`) to optimize memory usage and API requests.
* **Regex-Powered UI:** Transforms raw LLM outputs into an interactive HTML/CSS experience with custom hover tooltips for error correction.

## 🛠️ Tech Stack & Architecture
* **Frontend:** Streamlit (with custom CSS/JS injection for dynamic DOM manipulation and word tracking).
* **Backend:** Python
* **Model Inference:** Hugging Face Serverless Inference API (Primary: `Qwen/Qwen2.5-72B-Instruct`, Fallback: `32B-Instruct`).
* **Document Processing:** `python-docx` for parsing uploaded Word documents.
* **Deployment:** Streamlit Community Cloud.

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/cogism/esl-writing-mentor.git](https://github.com/cogism/esl-writing-mentor.git)
   cd esl-writing-mentor
