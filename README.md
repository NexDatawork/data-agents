<p align="center">
  <img src="assets/banner.png" alt="NexDatawork Banner" width="100%"/>
</p>

<div align="center">



<h1 style="margin-bottom:0; border-bottom:none;">
  <a
    href="https://www.nexdatawork.io/blank"
    style="color:#5A2AB8; text-decoration:none;"
  >
    NexDatawork
  </a>
</h1>


 <h2 style="margin-top:0;">
  Building the Data Infrastructure for AI  
 </h2>

 <div align='center'>
 <a href="https://github.com/NexDatawork/data-agents/pulls"><img alt = "pull requests" src = "https://img.shields.io/github/issues-pr-closed/NexDatawork/data-agents?label=pull%20requests&labelColor=3834B6&color=5A2AB8"/></a> 
<a href="https://github.com/NexDatawork/data-agents/blob/main/LICENSE"><img alt="LICENSE" src="https://img.shields.io/badge/license-Apache%202.0-blueviolet?style=flat&labelColor=3834B6&color=5A2AB8"/></a>
<a href="https://www.nexdatawork.io" target="_blank"><img alt="Website" src="https://img.shields.io/badge/Website-nexdatawork.io-5A2AB8?style=flat&labelColor=3834B6"/></a>
<a href="https://discord.gg/Tb55tT5UtZ"><img src="https://img.shields.io/badge/Discord-Join%20Community-7289DA?logo=discord&logoColor=white&labelColor=3834B6&color=5A2AB8" alt="Discord"/></a>
<a href="https://github.com/NexDatawork/data-agents/stargazers"><img src="https://img.shields.io/github/stars/NexDatawork/data-agents?style=social" alt="GitHub Stars"></a>
<a href="https://huggingface.co/NexDatawork">
  <img alt="Hugging Face" src="https://img.shields.io/badge/Hugging%20Face-Models%20%26%20Datasets?logo=huggingface&labelColor=3834B6&color=5A2AB8">
</a>


 </div>

</div>
An open-source, no-code agentic AI for building and evolving data layers for AI/ML. The open source repo includes a playground and sandbox environment for testing, experimentation, and community contributions.

## About

[NexDatawork](https://www.nexdatawork.io) builds a no-code, agentic AI that creates, maintains, and evolves the data layer required for AI/ML adoption.

It supports multiple data engineering and analytics workflows, including **multi-source data extraction**, **schema inference & metadata capture**, **query creation**, and **automated feature engineering**. 

The open source project includes a Hugging Face playground as a sandbox environment where users can experiment with the data agent, and a notebook for contributors to validate use cases and contribute improvements through pull requests.

## Trying out the Demo on Hugging Face

You can test the NexDatawork data agent directly in the Hugging Face sandbox without any local setup requirment. You can:
- Upload CSV, or JSON files
- Ask questions about your uploaded dataset
- View the explainable agent's reasoning and ETL steps

> Important Note: The Hugging Face demo is intended purelty for experimentation, testing and demonstration purposes only, and is not reflective of the final product's full capabilities and features.


## Run the Notebook

To understand how the data agent works step by step, you can run the Jupyter notebook included in this repository, in which each cell shows respective reasoning and outputs, and is primarily helpful for debugging the agent logic.


## Contributing via the Notebook

Contributors are welcome to:
- Improve the agent's various prompts
- Add new helpful tools (such as ETL, SQL, or web enrichments)
- Experiment with the UI or implement certain workflow changes

Note: You can attempt to submit adequate changes by opening a pull request.


## Table of contents
 * [Features & Workflow ](#features--workflow)
 * [Architecture](#architecture)
 * [Use Case](#use-case)
 * [Requirements & Starting Procedures](#requirements--starting-procedures)
 * [License](#license)
 * [Contributing](#contributing)


## <a name='features--workflow'></a>Features & Workflow

### Features

 - Display of reasoning
 - Simple Dashboard and Export
 - Seamless workflow set-up
 - Contextual intelligence
 - Chat-bot for refining the results

### Workflow




## <a name='architecture'></a>Architecture



## <a name='use-case'></a>Use Case




### Requirenments
 * [Node.js](https://nodejs.org/en)
 
 In order to run the programme Supabase and OpenAI API keys are needed.
 
 * [Supabase](https://supabase.com/)
 * [OpenAI](https://platform.openai.com/docs/overview)


### Environment Variables

To run this project, you will need to add the following environment variables to your [.env](.env.example) file

`NEXT_PUBLIC_SUPABASE_URL`

`NEXT_PUBLIC_SUPABASE_ANON_KEY`

`OPENAI_API_KEY`

### Quickstart

In order to start working with the program run the following code:
```bash
git clone https://github.com/NexDatawork/data-agents.git
cd data-agents
cp .env.example .env

Fill the URL and APIs in the environment file as shown in the [.env.example](.env.example).

When starting the program for the first time, run this code in your command line:

```bash
npm install
```

Afterwards the programme can be started as follows:
```bash
npm run dev
```



## <a name='contributing'></a>Contributing

Contributions are always welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for ways to get started.

## <a name='license'></a>License

This project is licensed under [the Apache-2.0 license](LICENSE).


## How to Try and Contribute

### Try the App
Users can test the application directly in the Hugging Face sandbox without any local setup. 

### Run the Notebooks
The project includes Jupyter notebooks that allow users to run the code step by step and observe results line by line. 

### Contribute to the Project
Contributors are welcome to improve the project by modifying existing notebook files. 
