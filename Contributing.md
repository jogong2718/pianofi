### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.10+
- AWS CLI configured with SSO or local keys

### Local Setup

1.  Clone the repository:

    ```bash
    git clone https://github.com/jogong2718/pianofi.git
    cd pianofi
    ```

2.  Create necessary environment files in these places:

    - `frontend/.env.local`
    - `packages/pianofi_config/.env`

3.  Log in to AWS SSO profile:

    ```bash
    ./dev-start.sh
    ```

    This script will also start the development environment using Docker Compose.
    Contact devs for the script.

4.  The services will be available at:
    - Frontend: `http://localhost:3000`
    - Backend API: `http://localhost:8000`
