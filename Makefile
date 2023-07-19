include item_warehouse/.env
export

api:
	clear
	poetry run uvicorn item_warehouse.src.app.main:app --reload --env-file item_warehouse/.env

api-clean:
	clear
	rm sql_app.db || :
	make api

vscode-shortcut-1:
	make api

vscode-shortcut-2:
	make api-clean
