## Demo datasets

This folder contains demo-friendly CSV datasets for testing and showcasing the data agent.

### `workflow_painpoints_demo.csv`
- **use case**: Analyze delays and errors across steps in a product demo workflow.
- **key columns**:
  - `workflow_id`: Identifier for a demo workflow run.
  - `step_name`: Name of the workflow step (e.g. `data_upload`, `data_cleaning`).
  - `step_order`: Order of the step within the workflow.
  - `time_spent_minutes`: Time spent on the step.
  - `had_error`: Boolean flag indicating if an error occurred.
  - `pain_point`: Short description of the pain point, if any.

### `cafe_sales.csv`
- **use case**: Explore point-of-sale transaction data for a small cafe.
- **key columns**:
  - `transaction_id`: Unique transaction identifier.
  - `date`: Transaction date.
  - `product_category`: High-level category (e.g. `coffee`, `food`).
  - `item_name`: Purchased item name.
  - `quantity`: Number of units sold.
  - `unit_price`: Price per unit.
  - `total_price`: Total amount for the line item.

### `spotify_churn_dataset.csv`
- **use case**: Model user churn for a music streaming service.
- **key columns**:
  - `user_id`: Unique user identifier.
  - `country`: User’s country.
  - `subscription_type`: Plan type (e.g. `free`, `premium`).
  - `monthly_listening_hours`: Total hours listened in the last month.
  - `skips_per_hour`: Average track skips per hour.
  - `support_tickets_last_90d`: Number of support tickets opened in the last 90 days.
  - `is_churned`: Boolean target indicating if the user churned.

### `Walmart.csv`
- **use case**: Analyze retail sales patterns across stores and departments.
- **key columns**:
  - `store`: Store identifier.
  - `dept`: Department identifier.
  - `date`: Week start date.
  - `weekly_sales`: Weekly sales amount.
  - `is_holiday`: Flag indicating if the week includes a holiday period.

### `customer_support_tickets.csv`
- **use case**: Monitor support team workload, SLAs, and customer satisfaction.
- **key columns**:
  - `ticket_id`: Unique ticket identifier.
  - `created_at`: Ticket creation timestamp.
  - `channel`: Support channel (e.g. `email`, `chat`, `phone`, `web`).
  - `customer_id`: Customer identifier.
  - `priority`: Ticket priority (`Low`, `Medium`, `High`).
  - `status`: Current status (e.g. `Open`, `Resolved`, `Escalated`, `Closed`).
  - `category`: Ticket category (e.g. `Billing`, `Technical Issue`, `Outage`).
  - `agent_id`: Assigned agent identifier (may be empty if unassigned).
  - `resolution_time_minutes`: Time to resolution in minutes, if resolved.
  - `satisfaction_rating`: Post-resolution customer satisfaction score (1–5), if provided.

### `product_reviews_demo.csv`
- **use case**: Analyze product review sentiment and quality across channels.
- **key columns**:
  - `review_id`: Unique review identifier.
  - `product_id`: Identifier of the reviewed product.
  - `product_name`: Human-readable product name.
  - `customer_id`: Customer identifier.
  - `review_date`: Date the review was created.
  - `rating`: Star rating (typically 1–5).
  - `title`: Short review title.
  - `review_text`: Full text of the review.
  - `verified_purchase`: Boolean flag indicating if the purchase was verified.
  - `source`: Review source (e.g. `website`, `mobile_app`, `third_party`).


