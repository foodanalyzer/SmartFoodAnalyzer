# Import ALL models here so SQLAlchemy registers them before create_all() runs.
# Order matters — parent tables before child tables (FK dependencies).

from app.models.user           import User
from app.models.user_goals     import UserGoals
from app.models.nutrition_db   import NutritionDB
from app.models.meal_logs      import MealLog
from app.models.analysis_tasks import AnalysisTask
