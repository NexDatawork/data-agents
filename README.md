<p align="center">
  <img src="assets/banner.png" alt="NexDatawork Banner" width="100%"/>
</p>

<div align="center">

 <h1 style="margin-bottom:0; border-bottom:none;">
   <a href="https://www.nexdatawork.io/blank">
     NexDatawork
   </a>
 </h1>

 <h2 style="margin-top:0;">
  An AI data agent for data engineering and analytics without writing code 
 </h2>

 <div align='center'>
 <a href="https://github.com/NexDatawork/data-agents/pulls"><img alt = "pull requests" src = "https://img.shields.io/github/issues-pr-closed/NexDatawork/data-agents?label=pull%20requests&labelColor=blue"/></a> 
 <a href="https://github.com/NexDatawork/data-agents/blob/main/LICENSE"><img alt = "LICENSE" src = "https://img.shields.io/badge/license-blue"/></a> 
 <a href = "https://discord.gg/Tb55tT5UtZ"><img src="https://img.shields.io/badge/Discord-Join%20Community-7289DA?logo=discord&logoColor=white" alt="Discord"></a>
 <a href="https://github.com/NexDatawork/data-agents/stargazers"><img src="https://img.shields.io/github/stars/NexDatawork/data-agents?style=social" alt="GitHub Stars"></a>


 </div>

</div>
A data agent designed for data analysis specified for particular tasks, quick visualisation and built for adapting for specific requirenments.


## Table of contents
 * [Features & Workflow ](#features--workflow)
 * [Architechture](#architecture)
 * [Use Case](#use-case)
 * [Requirenments & Starting Procedures](#requirenments--starting-procedures)
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


**Upload your data**

Choose the **Data Upload** menu and choose a csv file from your computer or drag and drop it in the menu.

**Specify what you expect from the result**


In the windows below choose an **Industries**, **Topics** and **Requirenments** for better results. You can add comments in a seperate window.

<image src='assets/image.png' alt='uploading data' width=250>

**Receive the analysed data**

In the **Data brain** tab you can see the summary, insights and description of the data.

In the **Dashboard** tab you can see the the graphs of the graphs of some distributions as well as summary.

In the **Chat** tab you can ask the bot about the details of the data.

<image src='assets/image-1.png' alt='uploading data' width=300>


## <a name='architecture'></a>Architecture


## <a name='use-case'></a>Use Case

After the analysis is completed the results are received in two tabs: **Data Brain** and **Dashboard**.

### Data Brain
1) General overview of the data is presented as well as the methodology of approaching the dataset

<p align='center'>
<image src='assets/executive_summary.png' alt='executive summary' width=500>
</p>

2) Recommendations on possible aspects of the data are generated

<p align='center'>
<image src='assets/business_insights.png' alt='business insights' width=500>
</p>

3) a conclusive overview of the data and statistical insights are presented



<p align='center'>
<image src='assets/Methodology.png' alt='Methodology' width=500 />
<image src='assets/Data_evidence.png' alt='Data evidence' width=500 />
<image src='assets/Statistical_insights.png' alt='Statistical insights' width=500 />
<image src='assets/categorical_distribution.png' alt='categorical distribution' width=500 />
</p>


### Dashboard

Brief overview of the data with only the most important metrics and figures, such as:
 * file information
<p align='center'>
<image src='assets/file_information.png' alt='file_information' width=500 />
</p>

 * number of columns of each type (numerical, categorical and temporal)

 * data quality and statistical summary
<p align='center'>
 <image src='assets/analysis_summary.png' alt='analysis_summary' width=500 />
</p>

Finally, graphs of the most important variables are presented.
<p align='center'>
 <image src='assets/graph1.png' alt='graph1' width=225 />
 <image src='assets/graph2.png' alt='graph2' width=250 />
 <image src='assets/graph3.png' alt='graph3' width=225 />
</p>

## <a name='requirenments--starting-procedures'></a>Requirenments & Starting Procedures

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



## <a name='contributing'></a>Contributing

Contributions are always welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for ways to get started.

## <a name='license'></a>License

This project is licensed under [the Apache-2.0 license](LICENSE).



