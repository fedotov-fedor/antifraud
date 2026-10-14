# IEEE-CIS Fraud Detection

Учебный проект по поиску мошеннических транзакций на данных соревнования [IEEE-CIS Fraud Detection](https://www.kaggle.com/competitions/ieee-fraud-detection).

Цель проекта - пройти полный цикл решения задачи бинарной классификации: от EDA и baseline до подбора параметров, проверки на отложенном периоде и интерпретации модели.

Основная метрика - **ROC-AUC**. Дополнительно я использовал PR-AUC, потому что доля мошеннических транзакций составляет всего около 3.5%.

## Результат

| Этап | Выборка | ROC-AUC | PR-AUC |
|---|---|---:|---:|
| DummyClassifier | validation fold 2 | 0.5000 | 0.0339 |
| Random Forest baseline | validation fold 2 | 0.8704 | 0.4415 |
| XGBoost baseline | validation fold 2 | 0.8815 | 0.4813 |
| XGBoost после feature engineering | среднее по двум фолдам | 0.88354 | 0.50902 |
| XGBoost после Optuna | среднее по двум фолдам | 0.90217 | 0.55038 |
| Финальная модель | локальный holdout | **0.90913** | **0.55475** |
| Финальная модель | Kaggle Private | **0.911611** | - |
| Финальная модель | Kaggle Public | **0.937537** | - |

Разница между локальным holdout и Private Score составила всего `0.00248`. Для меня это главный результат проекта: временная валидация достаточно точно оценила качество на закрытой части Kaggle test.

## Ход работы


1. EDA 
2. baseline 
3. feature engineering 
4. tuning 
5. final holdout 
6. Kaggle 
7. Интерпретация


### EDA и отбор признаков

- Объединил transaction- и identity-таблицы по `TransactionID`.
- Исследовал временную структуру, суммы транзакций и пропуски.
- Сократил 339 анонимных `V`-признаков до 108 представителей корреляционных групп.
- Обнаружил временной сдвиг между train и test.

### Валидация

Случайный split для этих данных не подходит: транзакции в train и test разделены по времени. Поэтому я использовал два временных фолда и gap в 30 дней.

| Fold | Train | Gap | Validation |
|---|---|---|---|
| 1 | дни 1–62 | 63–92 | 93–122 |
| 2 | дни 1–92 | 93–122 | 123–152 |
| Final | дни 1–122 | 123–152 | 153–182 |

Дни 153–182 не использовались при выборе признаков и гиперпараметров. Они были открыты только для финальной оценки.

### Модели

В качестве baseline я сравнил:

- DummyClassifier
- Random Forest
- XGBoost

XGBoost показал лучший результат, поэтому дальнейшие эксперименты проводились с ним.

### Feature engineering

Я отдельно проверял каждую группу признаков на двух временных фолдах.

Полезными оказались:

- циклические признаки часа и дня недели
- нормализация `D1`, `D2`, `D4`, `D10`, `D11`, `D15` относительно дня транзакции

Не дали устойчивого улучшения:

- логарифм и дробная часть `TransactionAmt`
- счётчики пропусков
- Исходные categorical в XGBoost
- frequency encoding выбранных идентификаторов

Frequency encoding улучшил ранний фолд, но ухудшил более поздний. Поэтому я отказался от него, несмотря на небольшой прирост средней метрики.

### Подбор параметров

Для настройки XGBoost использовалась Optuna: 15 trials, каждый оценивался на двух временных фолдах. Оптимизировался средний ROC-AUC, но при выборе также учитывались худший фолд и разрыв между train и validation.

Финальной стала конфигурация trial 13. Число деревьев `1758` было заранее рассчитано по best iteration двух development-фолдов, поэтому final holdout не использовался для early stopping.

### Интерпретация

Для финальной модели рассчитаны gain importance и TreeSHAP.

Основные наблюдения:

- наиболее важные признаки по SHAP: `C13`, `TransactionAmt`, `C1`, `card6`, `C14`, `D4`, `D3`
- при проверке 5% транзакций с самым высоким скором модель находит 58.98% fraud
- precision в этих 5% составляет 41.34%, lift относительно случайного отбора - 11.80
- сложнее всего модель работает с `ProductCD=W` и транзакциями без identity-информации


## Структура проекта

```text
notebooks/
├── 01_eda.ipynb
├── 02_baseline.ipynb
├── 03_feature_engineering.ipynb
├── 04_hyperparameter_tuning.ipynb
├── 05_final_evaluation.ipynb
├── 06_kaggle_submission.ipynb
└── 07_model_interpretation.ipynb

src/
└── feature_selection.py

submissions/
└── xgboost_trial13_full_train.csv
```


## Как запустить

Проект запускался на Python 3.14. Основные библиотеки: pandas, NumPy, scikit-learn, XGBoost, Optuna, Matplotlib и Seaborn.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install pandas numpy scikit-learn xgboost optuna matplotlib seaborn jupyter
```

Скачайте данные со страницы соревнования и положите файлы в папку `data`:

```text
data/
├── train_transaction.csv
├── train_identity.csv
├── test_transaction.csv
├── test_identity.csv
└── sample_submission.csv
```

После этого запустите Jupyter из папки с ноутбуками:

```bash
cd notebooks
jupyter lab
```

Ноутбуки нужно выполнять по порядку. Самые долгие этапы - подбор гиперпараметров и повторное обучение моделей в feature engineering.


## Что бы я улучшил

- Добавить агрегаты по картам, адресам и email-доменам, рассчитанные без утечки из будущего
- Отдельно исследовать транзакции `ProductCD=W` и строки без identity
- Проверить калибровку вероятностей на новом временном периоде
- Сравнить XGBoost с LightGBM или CatBoost на той же схеме валидации
- После стабильного сравнения отдельных моделей проверить blending или stacking

Главный вывод проекта: в задаче с временным сдвигом корректная схема валидации оказалась важнее случайного прироста Public Score.
