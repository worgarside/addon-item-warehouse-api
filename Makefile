pynguin-%:
	cd item_warehouse/src/app && \
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
	cd item_warehouse/src/app/ && \
	poetry run uvicorn main:app --reload --env-file ../../.env

api-clean:
	clear
	rm sql_app.db || :
	make api

docker:
	cd item_warehouse && \
	docker-compose --verbose up --build


# VSCode Shortcuts #

vscode-shortcut-1:
	make api

vscode-shortcut-2:
	make api-clean

vscode-shortcut-3:
	make docker
