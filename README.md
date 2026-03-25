# daily-arXiv-ai-enhanced

> Your AI-powered daily digest of arXiv papers - making research reading smarter and more personalized!

This innovative tool transforms how you stay updated with arXiv papers by combining automated crawling with AI-powered summarization.

## Screenshots

<img src="images/index.png" alt="main-page" width="800">

## How to use

1. Fork this repo to your own account
2. Go to: your-own-repo -> Settings -> Secrets and variables -> Actions
3. Go to Secrets. Secrets are encrypted and used for sensitive data
4. Create two repository secrets named `OPENAI_API_KEY` and `OPENAI_BASE_URL`, and input corresponding values.
5. Go to Variables. Variables are shown as plain text and are used for non-sensitive data
6. Create the following repository variables:
   1. `CATEGORIES`: separate the categories with ",", such as "cs.CL, cs.CV"
   2. `LANGUAGE`: such as "Chinese" or "English"
   3. `MODEL_NAME`: such as "deepseek-chat"
   4. `EMAIL`: your email for push to GitHub
   5. `NAME`: your name for push to GitHub
7. Go to your-own-repo -> Actions -> arXiv-daily-ai-enhanced
8. You can manually click **Run workflow** to test if it works well (it may take about one hour). By default, this action will automatically run every day. You can modify it in `.github/workflows/run.yml`
9. Set up GitHub pages: Go to your own repo -> Settings -> Pages. In `Build and deployment`, set `Source="Deploy from a branch"`, `Branch="main", "/(root)"`. Wait for a few minutes, go to https://\<username\>.github.io/daily-arXiv-ai-enhanced/.
