```python
import pandas as pd
import regex as re
import os
```


```python
df = pd.read_pickle('./70QA_QUIZ_BANK_02.pkl')
print(df['topic'].str.len().max())
```

    41
    


```python
set(df[df['chapter_no']==11]['topic'])
```




    set()




```python
test = df[df['topic'].apply(lambda x: (isinstance(x, str))==False)]
```


```python
def get_topic_name(current_topic):
    if isinstance(current_topic, str):
        return current_topic
    else:
        print(f"Type: {type(current_topic)}")
        print(f"Length: {len(current_topic)}")
        return current_topic[1]


df['topic'] = df['topic'].apply(get_topic_name)
    
```


```python
# df.to_pickle('./650QA_QUIZ_BANK_01.pkl', protocol=4)
```


```python
# df.to_pickle('./70QA_QUIZ_BANK_02.pkl', protocol=4)
```


```python
# pd.read_pickle('./70QA_QUIZ_BANK_02.pkl')
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
      <th>topic</th>
      <th>chapter_title</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>What is the primary benefit of using Google Cl...</td>
      <td>[It integrates natively with Django's developm...</td>
      <td>3</td>
      <td>Django Cloud Run Benefit</td>
      <td>Cloud Run 01</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>In a Dockerfile for a Django application, why ...</td>
      <td>[It ensures Django will start properly since a...</td>
      <td>4</td>
      <td>Django Dockerfile Requirements Order</td>
      <td>Cloud Run 01</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>When setting up a Django application for produ...</td>
      <td>[It automatically compresses all static files,...</td>
      <td>2</td>
      <td>Django Cloud Run DEBUG False</td>
      <td>Cloud Run 01</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>Which of the following is the correct command ...</td>
      <td>[ENTRYPOINT ["python", "manage.py", "collectst...</td>
      <td>5</td>
      <td>Django Dockerfile Collectstatic Command</td>
      <td>Cloud Run 01</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1</td>
      <td>What is the purpose of using whitenoise in a D...</td>
      <td>[It provides a required security layer between...</td>
      <td>4</td>
      <td>Django Cloud Run Whitenoise</td>
      <td>Cloud Run 01</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>65</th>
      <td>3</td>
      <td>What is the difference between is_staff and is...</td>
      <td>[is_staff allows viewing admin pages, while is...</td>
      <td>2</td>
      <td>Django User is_staff is_superuser</td>
      <td>Essential Django Authentication and Authorization</td>
    </tr>
    <tr>
      <th>66</th>
      <td>3</td>
      <td>Which class-based view is most appropriate for...</td>
      <td>[SignupView, RegistrationView, CreateView, Use...</td>
      <td>3</td>
      <td>Django Registration Class View</td>
      <td>Essential Django Authentication and Authorization</td>
    </tr>
    <tr>
      <th>67</th>
      <td>3</td>
      <td>If a user is redirected to the login page by t...</td>
      <td>[They are redirected to the homepage, They are...</td>
      <td>5</td>
      <td>Django login_required Redirect Behavior</td>
      <td>Essential Django Authentication and Authorization</td>
    </tr>
    <tr>
      <th>68</th>
      <td>3</td>
      <td>What's the best approach for implementing role...</td>
      <td>[Assign individual permissions directly to eac...</td>
      <td>4</td>
      <td>Django Role Based Access</td>
      <td>Essential Django Authentication and Authorization</td>
    </tr>
    <tr>
      <th>69</th>
      <td>3</td>
      <td>What is Django's AnonymousUser and when is it ...</td>
      <td>[A special user instance that AuthenticationMi...</td>
      <td>1</td>
      <td>Django AnonymousUser Purpose</td>
      <td>Essential Django Authentication and Authorization</td>
    </tr>
  </tbody>
</table>
<p>70 rows × 6 columns</p>
</div>




```python
df1 = pd.read_pickle('./650QA_QUIZ_BANK_01.pkl')
df1['topic'].apply(lambda x: type(x)).value_counts()
```




    topic
    <class 'str'>    665
    Name: count, dtype: int64




```python

```
