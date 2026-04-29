.PHONY: all python clean dev-install

DIST_DIR = dist

## all: 打包 Python wheel
all: python
	@echo ""
	@echo "✓ 打包完成！wheel 在 $(DIST_DIR)/"

## python: 打包 Python wheel
python:
	@echo "构建 Python wheel..."
	pip install build --quiet
	python -m build --wheel --outdir $(DIST_DIR)
	@ls $(DIST_DIR)/*.whl

## dev-install: 开发模式（editable）安装
dev-install:
	pip install -e .
	@echo "✓ editable 安装完成"

## clean: 删除构建产物
clean:
	rm -rf $(DIST_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ 清理完成"
