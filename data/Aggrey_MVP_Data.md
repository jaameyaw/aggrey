# Aggrey MVP Data

> Markdown mirror of `Aggrey_MVP_Data.xlsx`. All rows and source column names are preserved. The Excel workbook remains the canonical import source; this file is for developer review, search, and understanding, not a substitute for validated database imports.

**Dataset version:** `mvp_v1_3`  
**Menu model:** repeating weekly menu by ISO weekday (Monday = 1, Sunday = 7). Holiday sample rows (brunch and dinner) have a blank `day_of_week`.  
**Data:** 227 menu records, 10 hours rows, 11 holiday/break ranges, 11 metadata rows.

## Contents

- [Menus](#menus)
- [Hours](#hours)
- [Holidays and breaks](#holidays-and-breaks)
- [Metadata](#metadata)

## Menus

`menu_scope = weekly` repeats each week. `holiday_sample` is one shared provisional brunch menu and one shared provisional dinner menu (copied from Saturday), not assigned to any individual weekday. A row is one food item, and **all rows matching the requested day, meal, and station** belong to the same available menu.

| menu_scope | day_of_week | meal_type | station | food_item | display_order |
| --- | --- | --- | --- | --- | --- |
| weekly | 1 | breakfast | Breakfast | Scrambled Eggs | 1 |
| weekly | 1 | breakfast | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 1 | breakfast | Breakfast | Bacon | 3 |
| weekly | 1 | breakfast | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 1 | breakfast | Breakfast | Hash Brown Patty | 5 |
| weekly | 1 | breakfast | Breakfast | Veggie Sausage Patty | 6 |
| weekly | 1 | breakfast | Breakfast | French Toast | 7 |
| weekly | 1 | breakfast | Breakfast | Grits | 8 |
| weekly | 1 | breakfast | Breakfast | Classic Oatmeal | 9 |
| weekly | 2 | breakfast | Breakfast | Scrambled Eggs | 1 |
| weekly | 2 | breakfast | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 2 | breakfast | Breakfast | Pork Sausage Patty | 3 |
| weekly | 2 | breakfast | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 2 | breakfast | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 2 | breakfast | Breakfast | Tater Tots | 6 |
| weekly | 2 | breakfast | Breakfast | Maple Pancakes | 7 |
| weekly | 2 | breakfast | Breakfast | Grits | 8 |
| weekly | 2 | breakfast | Breakfast | Classic Oatmeal | 9 |
| weekly | 3 | breakfast | Breakfast | Scrambled Eggs | 1 |
| weekly | 3 | breakfast | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 3 | breakfast | Breakfast | Bacon | 3 |
| weekly | 3 | breakfast | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 3 | breakfast | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 3 | breakfast | Breakfast | Hash Brown Patty | 6 |
| weekly | 3 | breakfast | Breakfast | Pound Cake French Toast | 7 |
| weekly | 3 | breakfast | Breakfast | Grits | 8 |
| weekly | 3 | breakfast | Breakfast | Classic Oatmeal | 9 |
| weekly | 4 | breakfast | Breakfast | Scrambled Eggs | 1 |
| weekly | 4 | breakfast | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 4 | breakfast | Breakfast | Pork Sausage Link | 3 |
| weekly | 4 | breakfast | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 4 | breakfast | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 4 | breakfast | Breakfast | Tater Tots | 6 |
| weekly | 4 | breakfast | Breakfast | Pancake | 7 |
| weekly | 4 | breakfast | Breakfast | Grits | 8 |
| weekly | 4 | breakfast | Breakfast | Classic Oatmeal | 9 |
| weekly | 5 | breakfast | Breakfast | Scrambled Eggs | 1 |
| weekly | 5 | breakfast | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 5 | breakfast | Breakfast | Bacon | 3 |
| weekly | 5 | breakfast | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 5 | breakfast | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 5 | breakfast | Breakfast | Hash Brown Patty | 6 |
| weekly | 5 | breakfast | Breakfast | Buttermilk Pancake Mix | 7 |
| weekly | 5 | breakfast | Breakfast | Grits | 8 |
| weekly | 5 | breakfast | Breakfast | Classic Oatmeal | 9 |
| weekly | 1 | lunch | Main hot-food | BBQ Chicken | 1 |
| weekly | 1 | lunch | Main hot-food | Roasted Yellow Potatoes | 2 |
| weekly | 1 | lunch | Main hot-food | Sauteed Spinach | 3 |
| weekly | 1 | lunch | Main hot-food | Baked Beans | 4 |
| weekly | 1 | lunch | Special | Orange Chicken Stir Fry | 1 |
| weekly | 1 | lunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 1 | lunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 1 | lunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 1 | lunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 1 | lunch | Grill / sandwich | French Fries | 5 |
| weekly | 1 | lunch | Grill / sandwich | Onion Rings | 6 |
| weekly | 1 | lunch | Grill / sandwich | White Hamburger Bun | 7 |
| weekly | 1 | lunch | Pasta | Buffalo Chicken Pasta | 1 |
| weekly | 1 | lunch | Pizza | Cheese Pizza | 1 |
| weekly | 1 | lunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 1 | lunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 1 | lunch | Pizza | Margherita Pizza | 4 |
| weekly | 2 | lunch | Main hot-food | Stuffed Salmon | 1 |
| weekly | 2 | lunch | Main hot-food | Yellow Rice | 2 |
| weekly | 2 | lunch | Main hot-food | Steamed Broccoli | 3 |
| weekly | 2 | lunch | Main hot-food | Roast Butternut Squash | 4 |
| weekly | 2 | lunch | Special | Taco Bar | 1 |
| weekly | 2 | lunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 2 | lunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 2 | lunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 2 | lunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 2 | lunch | Grill / sandwich | French Fries | 5 |
| weekly | 2 | lunch | Grill / sandwich | Onion Rings | 6 |
| weekly | 2 | lunch | Grill / sandwich | White Hamburger Bun | 7 |
| weekly | 2 | lunch | Pasta | Rasta Pasta | 1 |
| weekly | 2 | lunch | Pizza | Cheese Pizza | 1 |
| weekly | 2 | lunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 2 | lunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 2 | lunch | Pizza | BBQ Chicken Pizza | 4 |
| weekly | 3 | lunch | Main hot-food | Southern Fried Chicken | 1 |
| weekly | 3 | lunch | Main hot-food | Baked Chicken | 2 |
| weekly | 3 | lunch | Main hot-food | THS Baked Mac & Cheese | 3 |
| weekly | 3 | lunch | Main hot-food | Candied Sweet Potato | 4 |
| weekly | 3 | lunch | Main hot-food | Vegetarian Collard Greens | 5 |
| weekly | 3 | lunch | Special | Baked Alfredo | 1 |
| weekly | 3 | lunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 3 | lunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 3 | lunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 3 | lunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 3 | lunch | Grill / sandwich | French Fries | 5 |
| weekly | 3 | lunch | Grill / sandwich | Onion Rings | 6 |
| weekly | 3 | lunch | Grill / sandwich | White Hamburger Bun | 7 |
| weekly | 3 | lunch | Pasta | Spiral Greek Chicken Pasta | 1 |
| weekly | 3 | lunch | Pizza | Cheese Pizza | 1 |
| weekly | 3 | lunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 3 | lunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 3 | lunch | Pizza | Cinnamon Dessert Pizza | 4 |
| weekly | 4 | lunch | Main hot-food | Fried Pork Chop | 1 |
| weekly | 4 | lunch | Main hot-food | White Rice | 2 |
| weekly | 4 | lunch | Main hot-food | Country Gravy | 3 |
| weekly | 4 | lunch | Main hot-food | Black-Eyed Peas | 4 |
| weekly | 4 | lunch | Main hot-food | Roasted Garlic Kale | 5 |
| weekly | 4 | lunch | Special | Turkey Pita Bar | 1 |
| weekly | 4 | lunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 4 | lunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 4 | lunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 4 | lunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 4 | lunch | Grill / sandwich | French Fries | 5 |
| weekly | 4 | lunch | Grill / sandwich | Onion Rings | 6 |
| weekly | 4 | lunch | Grill / sandwich | White Hamburger Bun | 7 |
| weekly | 4 | lunch | Pasta | Chicken Parmesan Pasta Bake | 1 |
| weekly | 4 | lunch | Pizza | Cheese Pizza | 1 |
| weekly | 4 | lunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 4 | lunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 4 | lunch | Pizza | Buffalo Chicken Calzone | 4 |
| weekly | 5 | lunch | Main hot-food | Fried Fish | 1 |
| weekly | 5 | lunch | Main hot-food | THS Cheese Grits | 2 |
| weekly | 5 | lunch | Main hot-food | Fried Okra | 3 |
| weekly | 5 | lunch | Main hot-food | Western Green Beans | 4 |
| weekly | 5 | lunch | Main hot-food | Hush Puppies | 5 |
| weekly | 5 | lunch | Special | Beef Nachos Grande | 1 |
| weekly | 5 | lunch | Grill / sandwich | All Beef Hot Dog | 1 |
| weekly | 5 | lunch | Grill / sandwich | Turkey Patty | 2 |
| weekly | 5 | lunch | Grill / sandwich | Veggie Burger | 3 |
| weekly | 5 | lunch | Grill / sandwich | French Fries | 4 |
| weekly | 5 | lunch | Grill / sandwich | Onion Rings | 5 |
| weekly | 5 | lunch | Grill / sandwich | White Hamburger Bun | 6 |
| weekly | 5 | lunch | Pasta | Pasta Bake | 1 |
| weekly | 5 | lunch | Pizza | Cheese Pizza | 1 |
| weekly | 5 | lunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 5 | lunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 5 | lunch | Pizza | Vegetarian Chorizo Pizza | 4 |
| weekly | 6 | brunch | Breakfast | Scrambled Eggs | 1 |
| weekly | 6 | brunch | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 6 | brunch | Breakfast | Pork Sausage Link | 3 |
| weekly | 6 | brunch | Breakfast | Turkey Sausage Patty | 4 |
| weekly | 6 | brunch | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 6 | brunch | Breakfast | Tater Tots | 6 |
| weekly | 6 | brunch | Breakfast | Blueberry Pancakes | 7 |
| weekly | 6 | brunch | Breakfast | Grits | 8 |
| weekly | 6 | brunch | Breakfast | Classic Oatmeal | 9 |
| weekly | 6 | brunch | Main hot-food | Blackened Chicken | 1 |
| weekly | 6 | brunch | Main hot-food | Creamy Penne Alfredo | 2 |
| weekly | 6 | brunch | Main hot-food | Marinated Spinach | 3 |
| weekly | 6 | brunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 6 | brunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 6 | brunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 6 | brunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 6 | brunch | Grill / sandwich | French Fries | 5 |
| weekly | 6 | brunch | Grill / sandwich | Onion Rings | 6 |
| weekly | 6 | brunch | Grill / sandwich | White Hamburger Bun | 7 |
| weekly | 6 | brunch | Pizza | Cheese Pizza | 1 |
| weekly | 6 | brunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 6 | brunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 7 | brunch | Breakfast | Scrambled Eggs | 1 |
| weekly | 7 | brunch | Breakfast | Scrambled Eggs with Cheese | 2 |
| weekly | 7 | brunch | Breakfast | Pork Sausage Link | 3 |
| weekly | 7 | brunch | Breakfast | Turkey Sausage | 4 |
| weekly | 7 | brunch | Breakfast | Veggie Sausage Patty | 5 |
| weekly | 7 | brunch | Breakfast | Hashbrowns | 6 |
| weekly | 7 | brunch | Breakfast | Buttermilk Pancake Mix | 7 |
| weekly | 7 | brunch | Breakfast | Grits | 8 |
| weekly | 7 | brunch | Breakfast | Classic Oatmeal | 9 |
| weekly | 7 | brunch | Grill / sandwich | Beef Patty | 1 |
| weekly | 7 | brunch | Grill / sandwich | All Beef Hot Dog | 2 |
| weekly | 7 | brunch | Grill / sandwich | Turkey Patty | 3 |
| weekly | 7 | brunch | Grill / sandwich | Veggie Burger | 4 |
| weekly | 7 | brunch | Grill / sandwich | Onion Rings | 5 |
| weekly | 7 | brunch | Grill / sandwich | White Hamburger Bun | 6 |
| weekly | 7 | brunch | Pizza | Cheese Pizza | 1 |
| weekly | 7 | brunch | Pizza | Pepperoni Pizza | 2 |
| weekly | 7 | brunch | Pizza | Roasted Vegetable Pizza | 3 |
| weekly | 1 | dinner | Dinner / turntable | Herb-Roasted Chicken | 1 |
| weekly | 1 | dinner | Dinner / turntable | Seasoned Rice | 2 |
| weekly | 1 | dinner | Dinner / turntable | Steamed Green Beans | 3 |
| weekly | 1 | dinner | Dinner / turntable | Roasted Sweet Potatoes | 4 |
| weekly | 2 | dinner | Dinner / turntable | Butter Chicken | 1 |
| weekly | 2 | dinner | Dinner / turntable | Curry Stew | 2 |
| weekly | 2 | dinner | Dinner / turntable | Steamed Rice (Jasmine) | 3 |
| weekly | 2 | dinner | Dinner / turntable | Garlic Naan | 4 |
| weekly | 3 | dinner | Dinner / turntable | Roasted Turkey | 1 |
| weekly | 3 | dinner | Dinner / turntable | Mushroom Cream Sauce | 2 |
| weekly | 3 | dinner | Dinner / turntable | Roasted Red Potatoes | 3 |
| weekly | 3 | dinner | Dinner / turntable | Basil Infused Broccoli | 4 |
| weekly | 3 | dinner | Dinner / turntable | THS Fried Napa Cabbage | 5 |
| weekly | 4 | dinner | Dinner / turntable | Old Bay Shrimp in Creole Butter Sauce | 1 |
| weekly | 4 | dinner | Dinner / turntable | White Rice | 2 |
| weekly | 4 | dinner | Dinner / turntable | Stewed Pinto Beans with Tomatoes and Onions | 3 |
| weekly | 4 | dinner | Dinner / turntable | Cajun Corn | 4 |
| weekly | 5 | dinner | Dinner / turntable | Savory Chicken | 1 |
| weekly | 5 | dinner | Dinner / turntable | Mashed Potatoes | 2 |
| weekly | 5 | dinner | Dinner / turntable | Sauteed Spinach and Roasted Cherry Tomatoes | 3 |
| weekly | 5 | dinner | Dinner / turntable | Lima Beans | 4 |
| weekly | 6 | dinner | Dinner / turntable | Beef Stroganoff | 1 |
| weekly | 6 | dinner | Dinner / turntable | Butter Egg Noodle | 2 |
| weekly | 6 | dinner | Dinner / turntable | Steamed Broccoli | 3 |
| weekly | 6 | dinner | Dinner / turntable | Oregano Roasted Carrots | 4 |
| weekly | 7 | dinner | Dinner / turntable | Creamy-Herb Salmon | 1 |
| weekly | 7 | dinner | Dinner / turntable | Wild Rice | 2 |
| weekly | 7 | dinner | Dinner / turntable | Steamed Yellow Squash | 3 |
| weekly | 7 | dinner | Dinner / turntable | Honey Roasted Carrots | 4 |
| holiday_sample |  | brunch | Breakfast | Scrambled Eggs | 1 |
| holiday_sample |  | brunch | Breakfast | Scrambled Eggs with Cheese | 2 |
| holiday_sample |  | brunch | Breakfast | Pork Sausage Link | 3 |
| holiday_sample |  | brunch | Breakfast | Turkey Sausage Patty | 4 |
| holiday_sample |  | brunch | Breakfast | Veggie Sausage Patty | 5 |
| holiday_sample |  | brunch | Breakfast | Tater Tots | 6 |
| holiday_sample |  | brunch | Breakfast | Blueberry Pancakes | 7 |
| holiday_sample |  | brunch | Breakfast | Grits | 8 |
| holiday_sample |  | brunch | Breakfast | Classic Oatmeal | 9 |
| holiday_sample |  | brunch | Main hot-food | Blackened Chicken | 1 |
| holiday_sample |  | brunch | Main hot-food | Creamy Penne Alfredo | 2 |
| holiday_sample |  | brunch | Main hot-food | Marinated Spinach | 3 |
| holiday_sample |  | brunch | Grill / sandwich | Beef Patty | 1 |
| holiday_sample |  | brunch | Grill / sandwich | All Beef Hot Dog | 2 |
| holiday_sample |  | brunch | Grill / sandwich | Turkey Patty | 3 |
| holiday_sample |  | brunch | Grill / sandwich | Veggie Burger | 4 |
| holiday_sample |  | brunch | Grill / sandwich | French Fries | 5 |
| holiday_sample |  | brunch | Grill / sandwich | Onion Rings | 6 |
| holiday_sample |  | brunch | Grill / sandwich | White Hamburger Bun | 7 |
| holiday_sample |  | brunch | Pizza | Cheese Pizza | 1 |
| holiday_sample |  | brunch | Pizza | Pepperoni Pizza | 2 |
| holiday_sample |  | brunch | Pizza | Roasted Vegetable Pizza | 3 |
| holiday_sample |  | dinner | Dinner / turntable | Beef Stroganoff | 1 |
| holiday_sample |  | dinner | Dinner / turntable | Butter Egg Noodle | 2 |
| holiday_sample |  | dinner | Dinner / turntable | Steamed Broccoli | 3 |
| holiday_sample |  | dinner | Dinner / turntable | Oregano Roasted Carrots | 4 |

## Hours

Serving windows use 24-hour local time. The schedule is selected using holiday/break overrides before falling back to weekend or weekday.

| schedule_type | meal_type | start_time | end_time |
| --- | --- | --- | --- |
| weekday | breakfast | 07:30 | 09:30 |
| weekday | lunch | 11:00 | 14:00 |
| weekday | lite_lunch | 14:00 | 15:00 |
| weekday | dinner | 17:00 | 20:00 |
| weekend | brunch | 10:30 | 13:30 |
| weekend | dinner | 17:00 | 20:00 |
| holiday | brunch | 10:30 | 13:30 |
| holiday | dinner | 17:00 | 20:00 |
| break | brunch | 10:00 | 11:00 |
| break | dinner | 16:00 | 18:00 |

## Holidays and breaks

Start and end dates are inclusive. `verification_status` and `notes` are reproduced as supplied. The virtual-classes period remains provisional.

| name | start_date | end_date | schedule_type | verification_status | notes |
| --- | --- | --- | --- | --- | --- |
| Labor Day | 2026-09-07 | 2026-09-07 | holiday | calendar_date; mvp_hours | Official campus closure. Default holiday hours. |
| Fall Break | 2026-10-15 | 2026-10-16 | break | calendar_date; latest_hours | Fall Break override uses break hours. |
| Thanksgiving Holiday | 2026-11-25 | 2026-11-27 | break | calendar_date; user_confirmed_hours | Uses Fall Break brunch 10:00-11:00 and dinner 16:00-18:00, per latest user clarification. Sample holiday brunch menu. |
| Virtual Classes, Reading Day & Exams | 2026-11-30 | 2026-12-12 | break | pending_confirmation | Temporary MVP template: use Fall Break hours (brunch 10:00-11:00; dinner 16:00-18:00). Actual schedule pending manager/school confirmation; replace when received. |
| Christmas Break | 2026-12-17 | 2027-01-01 | break | calendar_date; user_confirmed_hours | Uses Fall Break brunch 10:00-11:00 and dinner 16:00-18:00, per latest user clarification. Sample holiday brunch menu. |
| Martin Luther King Jr. Holiday | 2027-01-18 | 2027-01-18 | holiday | calendar_date; mvp_hours | Official college closure. Default holiday hours. |
| Spring Break | 2027-03-08 | 2027-03-12 | break | calendar_date; latest_hours | Spring Break override uses break hours. |
| Easter Holiday | 2027-03-26 | 2027-03-29 | holiday | calendar_date; mvp_hours | Official college closure. Default holiday hours. |
| Memorial Day Observance | 2027-05-31 | 2027-05-31 | holiday | calendar_date; mvp_hours | Official college closure. Default holiday hours. |
| Juneteenth Observance | 2027-06-18 | 2027-06-18 | holiday | calendar_date; mvp_hours | Official college closure. Default holiday hours. |
| Fourth of July Observance | 2027-07-05 | 2027-07-05 | holiday | calendar_date; mvp_hours | Official college closure. Default holiday hours. |

## Metadata

These are dataset settings and documented assumptions, not food offerings.

| key | value | notes |
| --- | --- | --- |
| dataset_version | mvp_v1_3 | Added the provisional holiday and break dinner sample (copied from Saturday dinner); other source data unchanged from mvp_v1_2. |
| timezone | America/New_York | College local time |
| menu_recurrence | weekly | Repeat weekly without tying menu items to calendar dates |
| update_policy | manual | Until manager provides an update process |
| lunch_station_count | 5 | Main hot-food, Special, Grill / sandwich, Pasta, Pizza |
| holiday_brunch_source | saturday_sample | Provisional holiday brunch menu |
| holiday_dinner_source | saturday_sample | Provisional holiday and break dinner menu |
| lite_lunch_menu_status | missing | Lite Lunch hours exist; food menu not supplied |
| thanksgiving_christmas_hours_rule | break | Same serving hours as Fall Break |
| virtual_classes_hours_status | break_template_provisional | Virtual classes and exams use the break schedule for MVP testing; manager confirmation is still pending. |
| summer_operations | reduced_schedule | Dates and specific arrangements pending confirmation |

## Usage notes

- PostgreSQL (`menus`, `hours`, `holidays`, `metadata`) is the source of truth at runtime. Use the Excel workbook or a controlled seed process for imports, **not manual copying from this Markdown table**.
- Do not attach service dates to weekly menu rows. Resolve the local date, select its ISO weekday, then query all matching rows.
- The holiday and break dinner (`holiday_sample` dinner rows) is a provisional copy of Saturday dinner. Always label it as a sample menu; do not describe it as confirmed.
- Lite Lunch serving hours exist, but its food menu has not been supplied.
- A provisional override is still an override in the current seed data, but student-facing messages must not imply it was manager-confirmed.
