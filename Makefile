clean:
	find . \( -name "node_modules" -o -name "build" -o -name "dist" -o -name ".next" \) -type d -exec rm -rf {} +


pynguin-%:
	@cd item_warehouse/src/app && \
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
	@cd item_warehouse/src/api/ && \
	poetry run uvicorn main:app --reload --env-file ../../.env

api-clean:
	clear
	rm sql_app.db || :
	make api

docker:
	@cd item_warehouse && \
	docker-compose --verbose up --build

install:
	$(MAKE) install-api
	$(MAKE) install-website

install-api:
	poetry install --all-extras --sync

install-website:
	@cd item_warehouse/src/website && \
	npm install

install-npm:
	@cd item_warehouse/src/website && \
	npm install $(filter-out $@,$(MAKECMDGOALS))

website-local:
	@cd item_warehouse/src/website && \
	npm run dev

# VSCode Shortcuts #

vscode-shortcut-1:
	make api

vscode-shortcut-2:
	make api-clean

vscode-shortcut-3:
	make docker

vscode-shortcut-4:
	make website-local

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
