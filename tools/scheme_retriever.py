"""
Scheme Retriever Tool - Vector search for government schemes.
Uses ChromaDB for semantic search of scheme descriptions.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from tools.base import BaseTool
from app.config import settings

# Try to import ChromaDB and sentence transformers
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Using fallback search.")


class SchemeRetriever(BaseTool):
    """
    Tool for semantic search of government schemes.
    Uses ChromaDB for vector storage and retrieval.
    """
    
    COLLECTION_NAME = "government_schemes"
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the scheme retriever.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        super().__init__(
            name="scheme_retriever",
            description="उपयोगकर्ता की query के आधार पर प्रासंगिक योजनाएं खोजता है"
        )
        
        self.persist_directory = persist_directory or str(
            Path(__file__).parent.parent / settings.chroma_persist_directory
        )
        
        self.client = None
        self.collection = None
        self.embedding_function = None
        
        if CHROMADB_AVAILABLE:
            self._initialize_chromadb()
    
    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        global CHROMADB_AVAILABLE
        try:
            # Create persist directory
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize client - use Settings to avoid http-only client error
            from chromadb.config import Settings
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Use multilingual embedding function
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.embedding_function,
                metadata={"description": "Government schemes for Indian citizens"}
            )
            
            # Initialize with default schemes if empty
            if self.collection.count() == 0:
                self._populate_default_schemes()
            
            logger.info(f"ChromaDB initialized with {self.collection.count()} schemes")
            
        except Exception as e:
            logger.warning(f"ChromaDB failed, using fallback search: {e}")
            CHROMADB_AVAILABLE = False
    
    def _populate_default_schemes(self) -> None:
        """Populate the collection with default schemes."""
        default_schemes = [
            {
                "id": "pm_kisan",
                "name": "प्रधानमंत्री किसान सम्मान निधि",
                "description": "किसान सम्मान निधि योजना के तहत किसानों को प्रति वर्ष ₹6,000 की वित्तीय सहायता दी जाती है। यह राशि तीन किस्तों में सीधे बैंक खाते में जमा होती है। छोटे और सीमांत किसान इस योजना के लिए पात्र हैं।",
                "keywords": "किसान, खेती, कृषि, आय सहायता, PM Kisan"
            },
            {
                "id": "pm_awas_gramin",
                "name": "प्रधानमंत्री आवास योजना ग्रामीण",
                "description": "ग्रामीण क्षेत्रों में बेघर और कच्चे/जीर्ण-शीर्ण घरों में रहने वाले परिवारों को पक्का मकान बनाने के लिए वित्तीय सहायता। मैदानी क्षेत्रों में ₹1.20 लाख और पहाड़ी क्षेत्रों में ₹1.30 लाख दिए जाते हैं।",
                "keywords": "मकान, घर, आवास, housing, पक्का मकान"
            },
            {
                "id": "ayushman_bharat",
                "name": "आयुष्मान भारत प्रधानमंत्री जन आरोग्य योजना",
                "description": "गरीब परिवारों के लिए ₹5 लाख तक का मुफ्त स्वास्थ्य बीमा। अस्पताल में भर्ती होने पर इलाज का खर्च सरकार वहन करती है। इसमें 1,500 से अधिक बीमारियों का इलाज शामिल है।",
                "keywords": "स्वास्थ्य, बीमा, इलाज, अस्पताल, health insurance"
            },
            {
                "id": "pm_ujjwala",
                "name": "प्रधानमंत्री उज्ज्वला योजना",
                "description": "गरीब परिवारों की महिलाओं को मुफ्त LPG गैस कनेक्शन। धुएं से मुक्त रसोई के लिए स्वच्छ ईंधन। पहला रिफिल और चूल्हा भी मुफ्त दिया जाता है।",
                "keywords": "गैस, LPG, रसोई, महिला, cooking gas"
            },
            {
                "id": "sukanya_samriddhi",
                "name": "सुकन्या समृद्धि योजना",
                "description": "बालिकाओं के भविष्य के लिए विशेष बचत योजना। 10 वर्ष से कम आयु की बालिका के नाम पर खाता खोला जा सकता है। उच्च ब्याज दर और आयकर में छूट मिलती है।",
                "keywords": "बेटी, बालिका, बचत, girl child, savings"
            },
            {
                "id": "pm_shram_yogi",
                "name": "प्रधानमंत्री श्रम योगी मान-धन",
                "description": "असंगठित क्षेत्र के श्रमिकों के लिए पेंशन योजना। 60 वर्ष की आयु के बाद ₹3,000 प्रतिमाह पेंशन। रिक्शा चालक, मजदूर, घरेलू कामगार आदि इसके लिए पात्र हैं।",
                "keywords": "पेंशन, मजदूर, श्रमिक, worker, pension"
            },
            {
                "id": "jan_dhan",
                "name": "प्रधानमंत्री जन धन योजना",
                "description": "गरीबों के लिए जीरो बैलेंस बैंक खाता। ₹2 लाख का दुर्घटना बीमा और RuPay डेबिट कार्ड मिलता है। ओवरड्राफ्ट सुविधा भी उपलब्ध है।",
                "keywords": "बैंक खाता, bank account, बीमा, RuPay"
            },
            {
                "id": "mudra_yojana",
                "name": "प्रधानमंत्री मुद्रा योजना",
                "description": "छोटे व्यवसाय शुरू करने के लिए बिना गारंटी के ₹10 लाख तक का ऋण। शिशु (₹50,000), किशोर (₹5 लाख), और तरुण (₹10 लाख) श्रेणियों में ऋण उपलब्ध।",
                "keywords": "ऋण, loan, व्यवसाय, business, स्वरोजगार"
            }
        ]
        
        ids = [s["id"] for s in default_schemes]
        documents = [f"{s['name']}. {s['description']} {s['keywords']}" for s in default_schemes]
        metadatas = [{"name": s["name"], "id": s["id"]} for s in default_schemes]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Populated {len(default_schemes)} default schemes")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for relevant schemes.
        
        Args:
            input_data: Contains 'query' for search
            
        Returns:
            Dict with matching schemes
        """
        query = input_data.get("query", "सरकारी योजना")
        n_results = input_data.get("n_results", 5)
        
        logger.info(f"Searching schemes for: {query}")
        
        if not CHROMADB_AVAILABLE or self.collection is None:
            return self._fallback_search(query)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            schemes = []
            for i, doc_id in enumerate(results["ids"][0]):
                schemes.append({
                    "id": doc_id,
                    "name": results["metadatas"][0][i].get("name", ""),
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": 1.0 - (i * 0.1)  # Approximate score
                })
            
            return {
                "success": True,
                "schemes": schemes,
                "query": query,
                "total_results": len(schemes)
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._fallback_search(query)
    
    def _fallback_search(self, query: str) -> Dict[str, Any]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        
        # Simple keyword matching
        all_schemes = [
            {"id": "pm_kisan", "name": "प्रधानमंत्री किसान सम्मान निधि", "keywords": ["किसान", "खेती", "कृषि"]},
            {"id": "pm_awas", "name": "प्रधानमंत्री आवास योजना", "keywords": ["मकान", "घर", "आवास"]},
            {"id": "ayushman", "name": "आयुष्मान भारत", "keywords": ["स्वास्थ्य", "इलाज", "बीमा"]},
            {"id": "ujjwala", "name": "उज्ज्वला योजना", "keywords": ["गैस", "रसोई", "महिला"]},
            {"id": "sukanya", "name": "सुकन्या समृद्धि", "keywords": ["बेटी", "बालिका", "बचत"]},
            {"id": "shram_yogi", "name": "श्रम योगी मान-धन", "keywords": ["पेंशन", "मजदूर", "श्रमिक"]},
        ]
        
        results = []
        for scheme in all_schemes:
            for keyword in scheme["keywords"]:
                if keyword in query_lower or query_lower in keyword:
                    results.append(scheme)
                    break
        
        # If no matches, return all
        if not results:
            results = all_schemes
        
        return {
            "success": True,
            "schemes": results[:5],
            "query": query,
            "total_results": len(results),
            "fallback": True
        }
    
    def add_scheme(self, scheme_data: Dict[str, Any]) -> bool:
        """Add a new scheme to the collection."""
        if not CHROMADB_AVAILABLE or self.collection is None:
            return False
        
        try:
            document = f"{scheme_data['name']}. {scheme_data.get('description', '')} {scheme_data.get('keywords', '')}"
            
            self.collection.add(
                ids=[scheme_data["id"]],
                documents=[document],
                metadatas=[{"name": scheme_data["name"], "id": scheme_data["id"]}]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add scheme: {e}")
            return False


# Singleton instance
scheme_retriever = SchemeRetriever()


def search_schemes(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for scheme search."""
    return scheme_retriever.execute(input_data)
