# CHANGELOG

## Create a new version

```sh
rm -rf dist/ build/
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
# create egg-info and dist folders
python3 -m build
python3 -m pip install --upgrade twine
# use __token__ auth
python3 -m twine upload -u __token__ dist/* --verbose
# enter token
```

## 2025-01-01

- Bump to 1.0.0

## 2024-01-18

- Create `figer` package
