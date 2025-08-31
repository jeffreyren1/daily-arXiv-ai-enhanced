# daily-arXiv-ai-enhanced

> Your AI-powered daily digest of arXiv papers - making research reading smarter and more personalized!

This innovative tool transforms how you stay updated with arXiv papers by combining automated crawling with AI-powered summarization.

## Screenshots

- Main page. Highlight the interested keywords and authors.

<img src="images/index.png" alt="main-page" width="800">

- Setting page. Set up keywords and authors and store them in your browser.

<img src="images/setting.png" alt="setting-page" width="600">

- Detail page. Show details of the paper you clicked.

<img src="images/details.png" alt="detail-page" width="500">

- Date select. Enable selecting a single date or a date range for filtering papers (**Notice: a large date range will show lots of papers, which may lead your browser to get stuck.**).

<img src="images/single-date.png" alt="single-date" width="300">
<img src="images/range-date.png" alt="range-date" width="300">

- Statistics page (*in developing*). Help you analyze papers. Extract keywords for papers in the day(s) you select. In addition, if you select a range of dates, the keyword trends will be illustrated. (Fortunately, selecting a large range of papers **will not** stuck your browser to be stuck because this page will not show all papers. It may take a few seconds to process the keywords.)

<img src="images/keyword.png" alt="single-date" width="600">
<img src="images/trends.png" alt="range-date" width="600">

## How to use

This repo will daily crawl arXiv papers about **cs.CV, cs.GR, cs.CL and cs.AI**, and use **DeepSeek** to summarize the papers in **Chinese**.
If you wish to crawl other arXiv categories, use other LLMs, or other languages, please follow the instructions.

**Instructions:**

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
9. Set up GitHub pages: Go to your own repo -> Settings -> Pages. In `Build and deployment`, set `Source="Deploy from a branch"`, `Branch="main", "/(root)"`. Wait for a few minutes, go to https://\<username\>.github.io/daily-arXiv-ai-enhanced/. Please see this [issue](https://github.com/jeffreyren1/daily-arXiv-ai-enhanced/issues/14) for more precise instructions.
