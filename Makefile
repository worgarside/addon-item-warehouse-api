api:
	rm sql_app.db || :
	poetry run uvicorn item_warehouse.src.app.main:app --reload --env-file item_warehouse/.env
