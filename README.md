# PianoFi - AI-Powered Piano Transcription with [WAT.ai](https://watai.ca/)

PianoFi is an advanced AI-powered music transcription service that turns any audio file into professional piano sheet music. Simply upload your audio, and our cutting-edge AI models will generate accurate piano transcriptions in multiple formats.

Visit us at [pianofi.ca](https://pianofi.ca)

## 🧏‍♂️ [Check out our full team!](https://github.com/jogong2718/pianofi/wiki/About-Us)

## 🎹 Features

- **AI-Powered Transcription**: Convert audio files (MP3, WAV, FLAC) to piano sheet music.
- **Advanced AI Models**: Choose between AMT (faster processing, better musicality) and PiCoGen (higher accuracy, currently in beta).
- **Customizable Difficulty**: Generate Easy, Medium, or Hard arrangements to suit your skill level.
- **Multiple Output Formats**: Download as MusicXML, MIDI, and PDF (coming soon).
- **Interactive Sheet Music Player**: View and play your transcriptions with synchronized audio playback.
- **Measure Navigation**: Click on any measure to jump directly to that section in the audio.
- **User Dashboard**: Track and manage all your transcriptions in one place.
- **Subscription Plans**: Choose a plan that fits your needs, with secure payments via Stripe.

## ⚡ How It Works

1.  **Upload Audio**: Upload any song or audio file in MP3, WAV, or FLAC format.
2.  **AI Processing**: Our advanced neural networks analyze and transcribe your music in minutes.
3.  **Get Sheet Music**: Download professional piano sheet music or view it in our interactive player.

## 🛠️ Technical Overview

PianoFi is built with a modern microservices architecture designed for scalability and performance.

### Key Technologies

- **Frontend**: Next.js, TypeScript, Tailwind CSS, OpenSheetMusicDisplay (OSMD)
- **Backend**: FastAPI, PostgreSQL, Redis, Supabase Auth
- **AI Models**: AMT-APC and PiCoGen (finetuned piano transcription models)
- **Audio Processing**: FluidSynth, FFmpeg, midi2audio
- **Infrastructure**: Docker, AWS (ECS, Fargate, EC2, S3), Stripe

## 🚀 Development

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.10+
- AWS CLI configured with SSO

### Local Setup

1.  Clone the repository:

    ```bash
    git clone https://github.com/jogong2718/pianofi.git
    cd pianofi
    ```

2.  Create necessary environment files based on the examples:

    - `frontend/.env.local`
    - `packages/pianofi_config/.env`

3.  Log in to AWS SSO profile:

    ```bash
    ./dev-start.sh
    ```

    This script will also start the development environment using Docker Compose.

4.  The services will be available at:
    - Frontend: `http://localhost:3000`
    - Backend API: `http://localhost:8000`

## 🏗️ Architecture Deep Dive

### Model Workers and acknowledgements

- **AMT Worker**: Optimized for faster transcription with excellent musicality. Runs on AWS Fargate for cost-effective, serverless scaling.
- **PiCoGen Worker**: Provides higher note and timing accuracy, ideal for complex piano pieces. Requires GPU and runs on dedicated EC2 instances within an ECS cluster.

### Data Flow

<img width="7680" height="4320" alt="pianofi us-east-1" src="https://github.com/user-attachments/assets/945cb4f3-9ce4-4229-81ac-8fa94cf567c1" />

1.  User uploads an audio file from the frontend.
2.  Frontend requests a pre-signed upload URL from the backend.
3.  The file is uploaded directly to an AWS S3 bucket.
4.  Backend creates a job in the database and enqueues it in Redis, targeting the appropriate worker (AMT or PiCoGen).
5.  The designated worker picks up the job, downloads the audio from S3, and performs AI transcription.
6.  The worker generates a MIDI file, converts it to MusicXML, and synthesizes a preview audio file (MP3).
7.  All generated artifacts are uploaded back to S3.
8.  The backend is notified, and the job status is updated in the database.
9.  The user sees the completed transcription in their dashboard and can view, play, and download the files.

## 🔗 Links

- **Website**: [pianofi.ca](https://pianofi.ca)
- **Contact**: [jonathan@pianofi.ca](mailto:jonathan@pianofi.ca) or [bruce@pianofi.ca](mailto:bruce@pianofi.ca)
- **Support**: Visit [pianofi.ca/contact](https://pianofi.ca/contact)

## 📜 License

© 2025 PianoFi. All rights reserved.
