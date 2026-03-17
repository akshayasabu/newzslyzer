# News-Slyzer Deployment Guide (Render)

Follow these steps to deploy your News-Slyzer Flask project on [Render](https://render.com/).

## 1. Prepare your GitHub Repository
- Initialize a git repository in your project folder if you haven't already.
- Push your code to a GitHub, GitLab, or Bitbucket repository.
- Ensure `requirements.txt` and `Procfile` are at the root of your repository.

## 2. Create a Web Service on Render
- Log in to your Render dashboard.
- Click **New +** and select **Web Service**.
- Connect your GitHub repository.
- **Service Name**: `news-slyzer` (or your choice).
- **Environment**: `Python 3`.
- **Region**: Select the region closest to your users.
- **Branch**: `main` (or your default branch).
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## 3. Configure Environment Variables
In the Render dashboard, go to the **Environment** tab and add the following variables:
- `FLASK_SECRET_KEY`: A long, random string.
- `FLASK_ENV`: `production`
- `NEWS_API_KEY`: Your NewsAPI key.
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID (if using Google Login).
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret.
- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USERNAME`: Your email address for sending notifications.
- `SMTP_PASSWORD`: Your email App Password.
- `SENDER_EMAIL`: Your email address.

## 4. Important Considerations
> [!IMPORTANT]
> **Database Persistence**: Render's free tier uses an ephemeral file system. This means your SQLite database (`aura.db`) will be reset every time the service restarts (e.g., during a new deployment).
> - For persistent data on the free tier, consider using an external database like **Render PostgreSQL**.
> - Alternatively, you can attach a **Persistent Disk** to your web service (paid feature).

## 5. Verify your Deployment
Once the build is complete, Render will provide a public URL (e.g., `https://news-slyzer.onrender.com`). Visit this URL to ensure your site is live!
