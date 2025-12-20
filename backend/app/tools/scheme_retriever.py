from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

SCHEMES = [
    "प्रधानमंत्री किसान योजना शेतकऱ्यांसाठी आर्थिक सहाय्य देते",
    "उज्ज्वला योजना महिलांना मोफत गॅस कनेक्शन देते",
    "आयुष्मान भारत आरोग्य विमा सुविधा पुरवते"
]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(SCHEMES)

def retrieve_scheme(query: str):
    q_vec = vectorizer.transform([query])
    scores = (vectors @ q_vec.T).toarray()
    idx = np.argmax(scores)
    return SCHEMES[idx]
