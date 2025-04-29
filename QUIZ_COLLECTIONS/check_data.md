```python
import pandas as pd
import regex as re
import os
```


```python
df1 = pd.read_pickle('./650QA_QUIZ_BANK_01.pkl')
df2 = pd.read_pickle('./70QA_QUIZ_BANK_02.pkl')
```


```python
df2['topic'].value_counts()
```




    topic
    Authentication        28
    Cloud Run Setup       21
    Container & Docker    21
    Name: count, dtype: int64




```python

```
