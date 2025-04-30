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
def options_contain(list_options, substring=''):
    substring = substring.lower()
    for option in list_options:
        if substring in option.lower():
            return True
    return False

def question_contains(question, substring=''):
    return substring in question.lower()

df1[df1['options'].apply(options_contain, substring='just before the closing')]

```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>chapter_no</th>
      <th>question_text</th>
      <th>options</th>
      <th>answerIndex</th>
      <th>tag</th>
      <th>IDX</th>
      <th>topic</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>284</th>
      <td>6</td>
      <td>When integrating third-party libraries like Bo...</td>
      <td>[Inside `{% comment %}` blocks to avoid render...</td>
      <td>5</td>
      <td>Static Assets Location</td>
      <td>284</td>
      <td>Templates</td>
    </tr>
  </tbody>
</table>
</div>




```python
df1['options'].iloc[284]
```




    ['Inside `{% comment %}` blocks to avoid rendering.',
     'Directly within the Django view functions.',
     'Inline within the main content block of each child template.',
     'Within custom template tags specifically designed for each library.',
     'In the `` for CSS and just before the closing `` tag for JavaScript, typically within the base template.']




```python

```
