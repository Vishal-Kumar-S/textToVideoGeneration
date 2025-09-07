
## How It Works: Step-by-Step

Here is a detailed breakdown of each step in the pipeline, including the key libraries and files involved.

### 1. Generate Script
-   **What it does:** Creates a video script based on the user's topic.
-   **User Input:** `Video Subject` (e.g., "The future of renewable energy").
-   **Tool/Library:** Google **Gemini**
-   **File Involved:** `app/services/llm.py`

### 2. Generate Keywords
-   **What it does:** Analyzes the script to extract relevant keywords for finding video clips.
-   **Tool/Library:** Google **Gemini**
-   **File Involved:** `app/services/llm.py`

### 3. Generate Voiceover
-   **What it does:** Converts the text script into a natural-sounding voiceover audio file (`.mp3`).
-   **User Input:** `Voice Selection`, `Voice Speed`.
-   **Tool/Library:** Microsoft Azure TTS (`edge-tts`)
-   **File Involved:** `app/services/voice.py`

### 4. Generate Subtitles
-   **What it does:** Creates a precisely timed subtitle file (`.srt`) for the voiceover.
-   **User Input:** `Enable/Disable Subtitles`.
-   **Tool/Library:**
    -   **Primary:** `edge-tts` (uses word boundaries from the voice generation step for high precision).
    -   **Fallback:** `faster-whisper` (an AI model that transcribes the audio if the primary method fails).
-   **File Involved:** `app/services/subtitle.py`

### 5. Download Video Clips
-   **What it does:** Searches for and downloads high-quality, royalty-free stock videos based on the generated keywords.
-   **Tool/Library:** **Pexels API** (`requests`)
-   **File Involved:** `app/services/material.py`

### 6. Combine Video Clips
-   **What it does:** Stitches the downloaded video clips together into a single, seamless video track that matches the duration of the voiceover.
-   **User Input:** `Video Aspect Ratio`, `Clip Duration`, `Video Concat Mode`.
-   **Tool/Library:** `moviepy`
-   **File Involved:** `app/services/video.py`

### 7. Assemble Final Video
-   **What it does:** This is the final step where all the pieces come together. It takes the combined video track and overlays the voiceover audio and the subtitles.
-   **Tool/Library:** `moviepy`
-   **File Involved:** `app/services/video.py`



## Important Notes & Project Structure

Here are some key details about the project's structure and behavior that every team member should know.

### File Organization

-   **`webui/Main.py`**: This is the main entry point for the application. It uses the **Streamlit** library to create the web-based user interface you interact with.
-   **`app/services/`**: This directory contains the core logic for each step of the video creation process (e.g., `llm.py` for AI, `video.py` for video editing).
-   **`storage/tasks/<task_id>/`**: This is where all the magic happens! For each video you generate, a unique folder is created. Inside, you will find all the generated assets:
    -   `script.json`: The AI-generated script and keywords.
    -   `audio.mp3`: The voiceover file.
    -   `subtitle.srt`: The subtitle file.
    -   `combined-1.mp4`: The stitched-together video clips without audio or subtitles.
    -   `final-1.mp4`: The final, completed video.
-   **`storage/materials/`**: Downloaded stock videos from Pexels are cached here to avoid re-downloading them for future projects.

### Performance & Generation Time

-   **Generation time is directly proportional to the length of your script.** A longer script results in a longer voiceover, which means more video clips need to be downloaded and processed.
-   **To manage processing time**, keep your scripts concise. A typical 60-second video script will be processed much faster than a 5-minute one.
-   The most time-consuming steps are **downloading video materials** and **rendering the final video** (`moviepy` processing).

### A Note on API Keys & Costs

-   The project uses the **Gemini API** for script/keyword generation and the **Pexels API** for video clips.
-   Be mindful that the Gemini API is a paid service. While it's generally inexpensive, generating very long or numerous scripts will incur costs.
-   The Pexels API is free, but it has rate limits. If you generate many videos in a short period, you might temporarily hit the limit. Our shared API keys are managed in the `.config.toml` file.


## Key Features & User Controls

This project gives the user significant control over the final output. Here are the key features you can customize through the UI:

| Feature             | User Control(s)                                                  | How it Works                                                                                             | File Involved             |
| :------------------ | :--------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------- | :------------------------ |
| **Voiceover**       | Voice Selection, Voice Speed                                     | You can choose from a wide range of voices and adjust the speaking rate to match the desired tone.         | `app/services/voice.py`   |
| **Subtitles**       | Enable/Disable, Font Size, Font Color, Stroke Width & Color      | Full control over the appearance of subtitles, allowing you to style them for better readability and aesthetic appeal. | `app/services/video.py`   |
| **Video Composition** | Video Aspect Ratio (e.g., 9:16 for shorts), Clip Duration        | You can define the video's orientation and control the maximum length of each individual clip.           | `app/services/video.py`   |
| **Background Music**  | BGM Selection, BGM Volume                                        | You can upload your own background music and adjust its volume to sit nicely behind the voiceover.       | `app/services/video.py`   |
| **Video Source**      | Pexels or Local Files                                            | The system can either download clips automatically from Pexels or use video files you provide from your local machine. | `app/services/material.py`|



## Getting Started

This guide will walk you through setting up and running the project on your local machine. You can choose to run it directly with Python or use Docker for a more isolated environment.

### Prerequisites

-   **Python 3.11**
-   **Docker (Recommended)**: For a containerized setup. If you don't have it, you can download it from the official Docker website.

---

### Method 1: Running with Docker (Recommended)

Using Docker is the easiest way to get started, as it handles all dependencies (including FFmpeg and ImageMagick) for you.

**Step 1: Clone the Repository**

```sh
git clone https://github.com/Vishal-Kumar-S/textToVideoGeneration.git
cd textToVideoGeneration
```

This project requires a `config.toml` file in the root directory to function. This file contains essential API keys and settings.

> **Important:** The `config.toml` file is intentionally not included in this GitHub repository for security reasons. You will receive this file separately from the repo owner.

Place the `config.toml` file you received into the root of the project folder. The application will not start without it.


**Step 2: Build the Docker Image**

You only need to do this once.

```sh
docker-compose build
```

**Step 3: Run the Docker Container**

This command starts the application inside a container. It mounts your local `config.toml` and `storage` directory into the container, so your configurations and generated videos persist even if the container is removed.

```sh
docker-compose up
```

The application will now be running. Open your browser to `http://localhost:8501` to use it.

-   To **stop** the container: `docker stop text-to-video-app`
-   To **restart** it later: `docker start text-to-video-app`


---
### Method 2: Running Locally with Python (Not Recommended)

Follow these steps if you prefer to run the project directly on your machine without Docker.

**Step 1: Clone the Repository**

```sh
git clone https://github.com/Vishal-Kumar-S/textToVideoGeneration.git
cd textToVideoGeneration
```


**Step 2: Add the Configuration File**

This project requires a `config.toml` file in the root directory to function. This file contains essential API keys and settings.

> **Important:** The `config.toml` file is intentionally not included in this GitHub repository for security reasons. You will receive this file separately from the repo owner.

Place the `config.toml` file you received into the root of the project folder. The application will not start without it.

**Step 3: Install Dependencies**

It's highly recommended to use a virtual environment to keep dependencies isolated.

```sh
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install all required Python packages
pip install -r requirements.txt
```

**Step 4: Run the Application**

Once the setup is complete, start the Streamlit web interface with the following command:

```sh
streamlit run ./webui/Main.py
```

Now, open your browser to `http://localhost:8501` to start creating videos!




