<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/header-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/header-light.svg">
  <img width="100%" alt="Banele Chakuma, Aspiring Data Engineer. Hello reader, welcome to my github profile, making a difference with tech." src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/header-dark.svg">
</picture>

</div>

---

<a name="how-i-got-started"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/how-i-got-started-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/how-i-got-started-light.svg">
  <img alt="How I Got Started" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/how-i-got-started-dark.svg">
</picture>
</h3>

My journey into tech began as a student at **WeThinkCode_**, a coding school with no lecturers
and no traditional classes. Instead, you learn by solving real problems alongside the people
around you — peer-to-peer, project by project, figuring things out together instead of being
taught from the front. It pushes you to grow fast: you learn to ask for help, explain what you
know to someone else, and keep going when there's no one to just hand you the answer. That
mindset — that growth is something you build *with* and *for* the people around you, not just
alone — has stuck with me since.

Part of that was working in a group on a brownfield project — inheriting someone else's
existing codebase instead of starting from scratch, and having to understand, maintain and
extend it the way it actually happens on the job. We worked the way real software teams do:
Agile, in sprints, using GitLab to build pipelines and Docker to containerize and package what
we built. We also used **CodeScene** to keep an eye on bottlenecks and run health checks on the
codebase, which made the need for proper unit, acceptance and end-to-end tests click in a way
no lecture could have. WeThinkCode_ sets it up this way deliberately — simulating a real
workplace, with its tools and its pace, so that by the time you're actually in one, none of it
is unfamiliar.

---

<a name="featured-project"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/featured-project-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/featured-project-light.svg">
  <img alt="Featured Project: SafeShelf Tembisa" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/featured-project-dark.svg">
</picture>
</h3>

<a href="https://github.com/BaneleChakuma/safeshelf-tembisa">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-card-light.svg">
  <img width="100%" alt="SafeShelf Tembisa: tracking food from the delivery truck to the shelf. View the repository." src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-card-dark.svg">
</picture>
</a>

A data pipeline that tracks food **from the delivery truck to the shelf** in Tembisa, tackling
two problems at once: expired or spoiled food sold in local stores, and the risk of delivery
trucks being hijacked.

- **Stores** record deliveries, **committee members** do shelf checks, **residents** report
  problems anonymously, and **trucks** send trip updates
- The pipeline validates and cleans the data, then builds daily reports from role-based SQL
  views, so each audience only ever sees what they're allowed to see
- **For the community**: a daily list of expired food to pull from shelves, a store scoreboard
  built only from verified findings, and supplier accountability for near-expiry deliveries
- **For truckers**: a police-only alert when a truck is running late or stops unexpectedly —
  while its GPS location is the most restricted data in the system, visible only to police and
  automatically deleted after 30 days

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-pipeline-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-pipeline-light.svg">
  <img width="100%" alt="SafeShelf pipeline. Store deliveries, committee shelf checks, anonymous resident reports and truck trip updates go through extract, validate, clean and load into a SQLite database. The committee view feeds the expired-food and near-expiry supplier reports, the store view feeds essentials about to expire, the community view feeds the store scoreboard, and the police view feeds late-truck and unexpected-stop alerts. Truck GPS is police-only and removed after 30 days." src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/safeshelf-pipeline-dark.svg">
</picture>

[github.com/BaneleChakuma/safeshelf-tembisa](https://github.com/BaneleChakuma/safeshelf-tembisa)

<details>
<summary><b>My MVP plan</b></summary>

**My MVP plan:** the smallest version that actually proves the idea isn't just "the pipeline
runs" — it's the first report landing. Once clean data is loading and producing the
expired-food and essentials-expiring reports, that's the MVP: the point where a committee
member could genuinely use it to pull bad stock off a shelf. Everything after that — the
scoreboard, supplier report, police alerts, privacy rules, one-command automation — builds on
that same foundation rather than being needed to prove the concept works.

</details>

---

<a name="languages-and-data"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/languages-and-data-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/languages-and-data-light.svg">
  <img alt="Languages & Data" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/languages-and-data-dark.svg">
</picture>
</h3>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/languages-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/languages-light.svg">
  <img alt="Python, SQL, SQLite" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/languages-dark.svg">
</picture>

<a name="tools-and-workflow"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/tools-and-workflow-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/tools-and-workflow-light.svg">
  <img alt="Tools & Workflow" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/tools-and-workflow-dark.svg">
</picture>
</h3>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/tools-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/tools-light.svg">
  <img alt="Git, GitHub Actions, pytest, IntelliJ IDEA" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/skills/tools-dark.svg">
</picture>

---

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/activity/activity-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/activity/activity-light.svg">
  <img width="100%" alt="My GitHub activity over the last 12 months: contributions, current and longest streak, a 26-week contribution map and my top languages" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/activity/activity-dark.svg">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/output/github-contribution-grid-snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/output/github-contribution-grid-snake.svg" />
  <img alt="Contribution snake animation" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/output/github-contribution-grid-snake.svg" />
</picture>

</div>

---

<a name="what-im-working-on"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/what-im-working-on-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/what-im-working-on-light.svg">
  <img alt="What I'm Working On" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/what-im-working-on-dark.svg">
</picture>
</h3>

- Building a data pipeline end-to-end: extract, validate, clean, load — with a real test suite driving the design
- Practicing schema design: keys, constraints, and role-based SQL views
- Learning data governance and privacy rules (POPIA) as first-class parts of a pipeline, not an afterthought
- Writing tests before the code they test — unit, acceptance and end-to-end

<!-- latest-commit:start -->
**Latest commit:** [Update USER\_STORIES.md to match the combined milestone](https://github.com/BaneleChakuma/safeshelf-tembisa/commit/ed1a187644c42aecdb6be5468a97caa3af0d4489) in [safeshelf-tembisa](https://github.com/BaneleChakuma/safeshelf-tembisa) · 20 Oct 2026
<!-- latest-commit:end -->

---

<a name="outside-of-code"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/outside-of-code-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/outside-of-code-light.svg">
  <img alt="Outside of Code" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/outside-of-code-dark.svg">
</picture>
</h3>

One of my favourite anime is **Solo Leveling**. What stays with me most is the idea that
becoming stronger is never just for your own sake — it's what makes you able to show up for
the people who matter to you.

---

<a name="connect-with-me"></a>
<h3>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/connect-with-me-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/connect-with-me-light.svg">
  <img alt="Connect with Me" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/headings/connect-with-me-dark.svg">
</picture>
</h3>

<div align="center">

<a href="https://github.com/BaneleChakuma">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/github-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/github-light.svg">
  <img alt="GitHub" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/github-dark.svg">
</picture>
</a>
<a href="https://www.linkedin.com/in/banele-chakuma-51301436b/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/linkedin-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/linkedin-light.svg">
  <img alt="LinkedIn: Connect" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/linkedin-dark.svg">
</picture>
</a>
<a href="mailto:banelechakuma@gmail.com">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/email-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/email-light.svg">
  <img alt="Email: banelechakuma@gmail.com" src="https://raw.githubusercontent.com/BaneleChakuma/BaneleChakuma/master/assets/connect/email-dark.svg">
</picture>
</a>

</div>
