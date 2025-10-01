# Contributing guidelines
Thank you for your contribution to the project! Any kind of feedback is greatly welcome. 

## Reporting bugs/Feature requests

For reporting bugs, please, visit the [Issue](https://github.com/NexDatawork/data-agents/issues/new?template=bug_report.yml) page and for suggesting features visit the [Feature requests](https://github.com/NexDatawork/data-agents/issues/new?template=feature_request.yml) page.


### Before filing an issue, please check if there are already similar issues tracked. 

For currently tracked bugs check the [bug report](https://github.com/NexDatawork/data-agents/issues) page.

For requested enhancements see the [feature requests](https://github.com/NexDatawork/data-agents/issues?q=is%3Aissue%20state%3Aopen%20label%3Aenhancement) page.


When filing an issue please include as much information as possible:

* A reproducible test case or a series of steps
* The version of the code used (commit ID)
* Any modifications made, that are relevant to the bug
* Anything about your environment or deployment

## Prerequisites

For running the program locally you need:
 - [Node.js](https://nodejs.org/en)
 - [Supabase URL](https://supabase.com/)
 - [Supabase API key](https://supabase.com/)
 - [OpenAI API key](https://platform.openai.com/docs/overview)

For more information check the [example of the environment file](.env.example).

## Getting started

In order to start working with the program run the following code:
```bash
git clone https://github.com/NexDatawork/data-agents.git
cd data-agents
cp .env.example .env
```
Fill the URL and APIs in the environment file as shown in the [.env.example](.env.example).

When starting the program for the first time, run this code in your command line:

```bash
npm install
```

Afterwards the programme can be started as follows:
```bash
npm run dev
```
