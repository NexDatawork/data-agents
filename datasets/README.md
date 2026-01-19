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

### `WHI_Inflation.csv`
- **use case**: Analyze inflation trends across countries and years, and explore relationships between inflation, economic indicators, and well-being metrics.
- **key columns**:
  - `Country`: Name of the country.
  - `Year`: Year of observation.
  - `Headline Consumer Price Inflation`: Overall consumer price inflation rate.
  - `Energy Consumer Price Inflation`: Inflation rate for energy-related consumer prices.
  - `Food Consumer Price Inflation`: Inflation rate for food-related consumer prices.
  - `Official Core Consumer Price Inflation`: Core inflation rate excluding volatile items such as food and energy.
  - `Producer Price Inflation`: Inflation rate of prices received by domestic producers.
  - `GDP deflator Index growth rate`: Growth rate of the GDP deflator, reflecting overall price changes in the economy.
  - `Continent/Region`: Geographic region or continent of the country.
  - `Score`: Overall well-being or happiness score associated with the country-year.
  - `GDP per Capita`: Gross domestic product per capita.
  - `Social support`: Measure of perceived social support.
  - `Healthy life expectancy at birth`: Expected number of healthy years at birth.
  - `Freedom to make life choices`: Measure of individual freedom in life decisions.
  - `Generosity`: Indicator of charitable behavior and generosity.
  - `Perceptions of corruption`: Measure of perceived corruption in government and institutions.

### `robotics_data.csv`
- **use case**: Analyze the impact of robotics adoption across industries over time, focusing on productivity gains, cost savings, workforce displacement, and training requirements.
- **key columns**:
  - `Year`: Year of observation.
  - `Industry`: Industry sector where robots are adopted (e.g. manufacturing, healthcare, logistics).
  - `Robots_Adopted`: Number of robots adopted in the given industry and year.
  - `Productivity_Gain`: Percentage increase in productivity attributed to robot adoption.
  - `Cost_Savings`: Estimated cost savings resulting from automation.
  - `Jobs_Displaced`: Number of jobs displaced due to robotics adoption.
  - `Training_Hours`: Total training hours required to upskill workers for working alongside robots.

### `robot_inverse_kinematics_dataset.csv`
- **use case**: Support inverse kinematics analysis and modeling for robotic manipulators by mapping end-effector positions and orientations to corresponding joint configurations.
- **key columns**:
  - `q1`: Joint angle of the first robot joint.
  - `q2`: Joint angle of the second robot joint.
  - `q3`: Joint angle of the third robot joint.
  - `q4`: Joint angle of the fourth robot joint.
  - `q5`: Joint angle of the fifth robot joint.
  - `q6`: Joint angle of the sixth robot joint.
  - `x`: X-coordinate of the end-effector position.
  - `y`: Y-coordinate of the end-effector position.
  - `z`: Z-coordinate of the end-effector position.


### `German_FinTechCompanies.csv`
- **use case**: Analyze the German FinTech ecosystem by examining company status, business segments, founding information, and geographic distribution.
- **key columns**:
  - `ID`: Unique identifier for the FinTech company.
  - `Name`: Commonly used name of the company.
  - `Status`: Current operational status of the company.
  - `Original German`: Original German-language company name.
  - `Founding year`: Year the company was founded.
  - `Founder`: Name of the company founders.
  - `Linkedin-Account Founder`: LinkedIn profile of the founder(s), if available.
  - `Legal Name`: Official registered legal name of the company.
  - `Legal form`: Legal structure of the company.
  - `Street`: Street address of the company headquarters.
  - `Postal code`: Postal code of the company address.
  - `City`: City where the company is located.
  - `Country`: Country where the company is registered.
  - `Register Number/ Company ID/ LEI`: Official registration number or legal entity identifier.
  - `Segment`: Primary FinTech market segment.
  - `Subsegment`: More specific business subcategory within the main segment.
  - `Bank Cooperation`: Indicator of cooperation with banks.
  - `Homepage`: Official company website URL.
  - `E-Mail`: Contact email address of the company.
  - `Insolvency`: Indicator of insolvency status.
  - `Liquidation`: Indicator of whether the company is in liquidation.
  - `Date of inactivity`: Date when the company became inactive, if applicable.
  - `Local court`: Local court responsible for company registration.
  - `Former name`: Previous name of the company, if applicable.

### `Fintech_user.csv`
- **use case**: Analyze user behavior, engagement, and churn patterns in a FinTech platform, including product usage, credit activity, and reward participation.
- **key columns**:
  - `user`: Unique identifier for a user.
  - `churn`: Indicator of whether the user has churned.
  - `age`: Age of the user.
  - `housing`: Indicator of the user’s housing status.
  - `credit_score`: Credit score of the user.
  - `deposits`: Total amount of deposits made by the user.
  - `withdrawal`: Total amount of withdrawals made by the user.
  - `purchases_partners`: Number or amount of purchases made with partner merchants.
  - `purchases`: Total number or amount of purchases.
  - `cc_taken`: Indicator of whether a credit card was taken by the user.
  - `cc_recommended`: Indicator of whether a credit card was recommended to the user.
  - `cc_disliked`: Indicator of whether the user disliked the recommended credit card.
  - `cc_liked`: Indicator of whether the user liked the recommended credit card.
  - `cc_application_begin`: Indicator of whether the user started a credit card application.
  - `app_downloaded`: Indicator of whether the mobile app was downloaded.
  - `web_user`: Indicator of whether the user uses the web platform.
  - `app_web_user`: Indicator of whether the user uses both app and web platforms.
  - `ios_user`: Indicator of whether the user uses the iOS app.
  - `android_user`: Indicator of whether the user uses the Android app.
  - `registered_phones`: Number of phone numbers registered by the user.
  - `payment_type`: Preferred payment method used by the user.
  - `waiting_4_loan`: Indicator of whether the user is waiting for a loan decision.
  - `cancelled_loan`: Indicator of whether the user cancelled a loan application.
  - `received_loan`: Indicator of whether the user received a loan.
  - `rejected_loan`: Indicator of whether the user’s loan application was rejected.
  - `zodiac_sign`: Zodiac sign of the user.
  - `left_for_two_month_plus`: Indicator of whether the user left for more than two months.
  - `left_for_one_month`: Indicator of whether the user left for one month.
  - `rewards_earned`: Total rewards earned by the user.
  - `reward_rate`: Reward rate associated with the user.
  - `is_referred`: Indicator of whether the user was referred by another user.

### `Electric_Vehicle_Population_Data.csv`
- **use case**: Analyze the distribution and characteristics of electric vehicles across regions, including vehicle types, manufacturers, model years, and eligibility for clean fuel programs.
- **key columns**:
- `VIN (1-10)`: First 10 characters of the vehicle identification number.County: County where the vehicle is registered.
- `City`: City where the vehicle is registered.
- `State`: State where the vehicle is registered.
- `Postal Code`: Postal (ZIP) code of the vehicle registration location.
- `Model Year`: Manufacturing year of the vehicle model.
- `Make`: Vehicle manufacturer.
- `Model`: Vehicle model name.
- `Electric Vehicle Type`: Type of electric vehicle (e.g. battery electric, plug-in hybrid).
- `Clean Alternative Fuel Vehicle (CAFV) Eligibility`: Eligibility status for clean alternative fuel vehicle programs.
- `Electric Range`: Estimated electric-only driving range of the vehicle.
- `Base MSRP`: Base manufacturer’s suggested retail price.
- `Legislative District`: Legislative district associated with the vehicle registration.
- `DOL Vehicle ID`: Department of Licensing vehicle identifier.
- `Vehicle Location`: Geographic location information for the vehicle.
- `Electric Utility`: Electric utility provider serving the vehicle’s location.
- `2020 Census Tract`: Census tract identifier based on the 2020 census.
