clean:
	find . \( -name "node_modules" -o -name "build" -o -name "dist" -o -name ".next" \) -type d -exec rm -rf {} +

pynguin-%:
	@cd item_warehouse_api/src && \
	DATABASE_URL=sqlite:///./pynguin.db \
	PYNGUIN_DANGER_AWARE=1 \
	pynguin -v \
		--project-path . \
		--output-path ../../test \
		--module-name $(*) \
		--assertion_generation SIMPLE \
		--algorithm MOSA

api:
	clear
	@cd item_warehouse_api/src && \
	poetry run uvicorn main:app --reload --env-file ../.env --host 0.0.0.0 --port 8002

api-clean:
	clear
	rm sql_app.db || :
	make api

docker:
	@cd item_warehouse_api && \
	docker-compose --verbose up --build

install:
	poetry install --all-extras --sync

# VSCode Shortcuts #

vscode-shortcut-1:
	make api

vscode-shortcut-2:
	make api-clean

vscode-shortcut-3:
	make docker

vscode-shortcut-4:
	@echo "Shortcut not defined"
	@exit 1

vscode-shortcut-5:
	@echo "Shortcut not defined"
	@exit 1

vscode-shortcut-6:
	@echo "Shortcut not defined"
	@exit 1

vscode-shortcut-7:
	@echo "Shortcut not defined"
	@exit 1

vscode-shortcut-8:
	@echo "Shortcut not defined"
	@exit 1

vscode-shortcut-9:
	@echo "Shortcut not defined"
	@exit 1

%:
	@:
