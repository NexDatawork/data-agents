# OpenGraph AI Repository Map

This document captures the current repository file structure and the purpose of each tracked project file.

Scope notes:
- Includes source, configs, docs, tests, examples, archive, and package metadata files.
- Excludes Git internals and Python cache artifacts.

## Root

- .DS_Store: macOS Finder metadata file (not part of runtime behavior).
- .env.example: template environment variables for local configuration.
- .gitignore: Git ignore rules for generated/local files.
- CODEOWNER: code ownership rules for reviews and approvals.
- LICENSE: MIT license text for project usage and distribution.
- README.md: primary project overview, quickstart, and architecture summary.
- pyproject.toml: Python package metadata, dependencies, CLI entrypoint, and pytest config.

## API (FastAPI)

- api/__init__.py: package marker for API module.
- api/main.py: FastAPI app entrypoint and router mounting.
- api/routes/__init__.py: route registry with health endpoint scaffold.

## CLI (Typer)

- cli/__init__.py: package marker for CLI module.
- cli/__main__.py: CLI root app definition, command registration, and version flag.
- cli/commands/__init__.py: package marker for CLI command group.
- cli/commands/demo.py: offline end-to-end demo command for text extraction and graph build.
- cli/commands/extract.py: text extraction command that calls LLM extractor and writes graph JSON.

## Engine (Core Python)

- engine/__init__.py: package marker for shared engine.
- engine/connectors/__init__.py: placeholder package marker for future external connectors.
- engine/embeddings/__init__.py: package marker for embeddings functionality.
- engine/embeddings/generator.py: placeholder module for embedding generation helpers.
- engine/extractors/__init__.py: package marker for extraction modules.
- engine/extractors/table_extractor.py: CSV table reader that returns rows as dictionaries.
- engine/extractors/text_extractor.py: text extraction helpers (offline regex mode and LLM-backed mode).
- engine/graphs/__init__.py: package marker for graph operations.
- engine/graphs/builder.py: graph construction utilities from records or extraction payloads.
- engine/graphs/query.py: graph query helpers (node lookup and neighbor traversal).
- engine/llm/__init__.py: package marker for LLM provider layer.
- engine/llm/provider.py: OpenAI chat completion wrapper and environment-based model selection.
- engine/schema/__init__.py: package marker for graph schema models.
- engine/schema/edge.py: edge dataclass schema for graph relationships.
- engine/schema/graph.py: in-memory graph container with node/edge mutation methods.
- engine/schema/node.py: node dataclass schema for graph entities.

## MCP Server (Node/TypeScript)

- mcp-server/index.ts: MCP server bootstrap scaffold and startup logging.
- mcp-server/package.json: Node package metadata, scripts, and TypeScript dev dependencies.
- mcp-server/tools/index.ts: placeholder MCP tool registry.

## Tests

- tests/test_extractors.py: unit tests for text extraction helpers.
- tests/test_graph_builder.py: unit tests for graph builder behavior.

## Examples (Current)

- examples/table_example.csv: sample CSV input used for table extraction demos.
- examples/text_example.txt: sample text input used for text extraction demos.

## Packaging Metadata

- opengraph_ai.egg-info/PKG-INFO: built package metadata snapshot.
- opengraph_ai.egg-info/SOURCES.txt: list of files included in package source distribution.
- opengraph_ai.egg-info/dependency_links.txt: package dependency links metadata.
- opengraph_ai.egg-info/entry_points.txt: installed CLI entrypoint mapping.
- opengraph_ai.egg-info/requires.txt: resolved package requirement list.
- opengraph_ai.egg-info/top_level.txt: top-level import packages in distribution.

## Archive (Legacy/Reference Materials)

- archive/CONTRIBUTING.md: older contribution instructions.
- archive/README_old.md: previous project README and historical context.
- archive/REQUIREMENTS.md: archived requirements and design notes.
- archive/components.json: archived UI/component configuration metadata.
- archive/requirements.txt: archived Python dependency list for legacy demos.
- archive/framework_demo_c.py: legacy full demo script with traced workflow and multi-task outputs.
- archive/demo_c_with_optional_fintech_csv_input.py: legacy demo script with optional FinTech CSV/PDF ingestion.

### Archive Assets

- archive/assets/Architecture updated.png: architecture diagram (updated revision).
- archive/assets/Architecture.png: architecture diagram (original revision).
- archive/assets/Data_evidence.png: data evidence visualization artifact.
- archive/assets/Methodology.png: methodology/process visualization artifact.
- archive/assets/Statistical_insights.png: statistical insights visualization artifact.
- archive/assets/analysis_summary.png: analysis summary visualization artifact.
- archive/assets/banner.png: project/demo banner image.
- archive/assets/business_insights.png: business insights visualization artifact.
- archive/assets/categorical_distribution.png: category distribution visualization artifact.
- archive/assets/executive_summary.png: executive summary visualization artifact.
- archive/assets/file_information.png: file information visualization artifact.
- archive/assets/graph1.png: example graph output image #1.
- archive/assets/graph2.png: example graph output image #2.
- archive/assets/graph3.png: example graph output image #3.
- archive/assets/image-1.png: miscellaneous archived image asset.
- archive/assets/image.png: miscellaneous archived image asset.
- archive/assets/public/placeholder-logo.png: placeholder logo image for archived UI.
- archive/assets/public/placeholder-logo.svg: placeholder logo vector for archived UI.
- archive/assets/public/placeholder-user.jpg: placeholder user avatar for archived UI.
- archive/assets/public/placeholder.jpg: generic placeholder image for archived UI.
- archive/assets/public/placeholder.svg: generic placeholder vector for archived UI.

### Archive Data

- archive/data/run_logs.jsonl: line-delimited JSON run history from archived demos.

### Archive Datasets

- archive/datasets/README.md: notes describing archived datasets.
- archive/datasets/Delinquency_prediction_dataset.xlsx: tabular dataset for delinquency/prediction experiments.
- archive/datasets/Fintech_user.csv: user-level FinTech demo dataset.
- archive/datasets/German_FinTechCompanies.csv: company-level FinTech reference dataset.
- archive/datasets/WHI_Inflation.csv: inflation/economic indicator dataset.
- archive/datasets/Walmart.csv: retail dataset for analysis demos.
- archive/datasets/cafe_sales.csv: cafe transaction dataset for analytics examples.
- archive/datasets/customer_support_tickets.csv: support ticket dataset for analysis workflows.
- archive/datasets/product_reviews_demo.csv: product reviews dataset for NLP/analysis demos.
- archive/datasets/robot_inverse_kinematics_dataset.csv: robotics inverse kinematics sample dataset.
- archive/datasets/robotics_data.csv: robotics telemetry/features dataset.
- archive/datasets/sample_file_upload.json: JSON sample file upload payload.
- archive/datasets/spotify_churn_dataset.csv: customer churn dataset for retention analysis demos.
- archive/datasets/workflow_painpoints_demo.csv: workflow pain-point dataset for process analysis.

### Archive Examples

- archive/examples/.DS_Store: macOS Finder metadata inside archived examples.
- archive/examples/.gradio/certificate.pem: local certificate artifact for archived Gradio setup.
- archive/examples/accuracy_threshold_script.py: legacy script for threshold/accuracy experimentation.
- archive/examples/agentic_ai_langchain_using_OPENAI.ipynb: legacy notebook demonstrating LangChain agentic flow.
- archive/examples/app.py: archived app entry script for demo interface.
- archive/examples/data_agent_demo.ipynb: archived notebook for data agent demonstrations.
- archive/examples/data_agent_demo.py: archived Python script for data agent demo workflow.
- archive/examples/database.db: SQLite database generated/used by archived SQL examples.
- archive/examples/requirements.txt: dependencies for archived examples.
- archive/examples/synthetic_data_generating.py: script for generating synthetic demo data.
- archive/examples/synthetic_dataset.csv: generated synthetic dataset in CSV form.
- archive/examples/synthetic_dataset.json: generated synthetic dataset in JSON form.

### Archive TE Agentic Demo

- archive/examples/demo_TE_Agentic/framework_demo_b.py: legacy TE framework demo (variant B).
- archive/examples/demo_TE_Agentic/framework_demo_v2.py: legacy TE framework demo (v2 variant).
- archive/examples/demo_TE_Agentic/requirements_demo.txt: dependencies for TE demo variant.
- archive/examples/demo_TE_Agentic/requirements_demo_b.txt: dependencies for TE demo B variant.
- archive/examples/demo_TE_Agentic/requirements_final.txt: consolidated/final dependency set for TE demos.

### Archive Synthetic Example Bundle

- archive/examples/synthetic/README.md: documentation for archived synthetic-data example bundle.
- archive/examples/synthetic/data/sample/dpd_sample.csv: sample synthetic CSV data file.
- archive/examples/synthetic/notebooks/notebooks_synthetic_data_generator.ipynb: notebook for synthetic data generation.

### Archive Source Package

- archive/src/__init__.py: package marker for archived source package.
- archive/src/agents/__init__.py: package marker for archived agent modules.
- archive/src/agents/coordinator.py: orchestration class that coordinates archived analysis/SQL/ETL/web agents.
- archive/src/agents/dataframe_agent.py: archived pandas DataFrame analysis agent implementation.
- archive/src/agents/etl_agent.py: archived ETL code-generation agent implementation.
- archive/src/agents/scraping_agent.py: archived web scraping agent implementation.
- archive/src/agents/sql_agent.py: archived SQL generation/execution agent implementation.
- archive/src/prompts/__init__.py: package marker for archived prompt templates.
- archive/src/prompts/analysis_prompts.py: prompt templates for archived DataFrame analysis agent.
- archive/src/prompts/scraping_prompts.py: prompt templates for archived web scraping agent.
- archive/src/prompts/sql_prompts.py: prompt templates for archived SQL agent.
- archive/src/utils/__init__.py: package marker for archived utility helpers.
- archive/src/utils/file_ops.py: archived CSV/file utility functions.
- archive/src/utils/llm.py: archived model factory helpers for Azure/OpenAI LangChain clients.
