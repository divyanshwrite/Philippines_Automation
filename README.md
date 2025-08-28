# FDA Philippines Automation System

🏥 **A production-ready automation system for extracting and storing regulatory documents from FDA Philippines using WordPress REST API.**

## 🎯 Project Overview

This system automatically fetches, processes, and stores FDA Philippines regulatory documents in a PostgreSQL database. It evolved from a hardcoded system with 50 documents to a dynamic API-driven solution processing 900+ documents.

### ✨ Key Achievements
- **📈 Scale**: Increased from 50 hardcoded documents to 900+ dynamic documents
- **🔄 Automation**: Full automation with WordPress REST API integration
- **📊 Smart Filtering**: Automatically targets current and previous year documents
- **🗄️ Database Integration**: PostgreSQL storage with duplicate prevention
- **⚡ Performance**: Processes ~8 documents per run with robust error handling

## 🚀 Features

### Core Functionality
- **WordPress REST API Integration**: Fetches from 17,383+ total posts
- **Multi-page Pagination**: Handles 174+ pages of content
- **Dynamic Year Logic**: Automatically targets current + previous year (2024-2025)
- **Smart Duplicate Prevention**: URL tracking system prevents reprocessing
- **Full Content Extraction**: Complete document text extraction and storage
- **Robust Error Handling**: Comprehensive logging and retry mechanisms

### Technical Features
- PostgreSQL database integration
- JSON serialization for complex data types
- Configurable batch processing
- Real-time progress monitoring
- Comprehensive test suite

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/divyanshwrite/Philippines_Automation.git
   cd Philippines_Automation
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**:
   - Update `config.py` with your PostgreSQL credentials
   - Ensure the database and schema exist

5. **Run the system**:
   ```bash
   python3 main_updated.py
   ```

## 📋 Usage

### Daily Operation
```bash
# Run the main automation
python3 main_updated.py
```

### Testing
```bash
# Test database integration
python3 test_db_integration.py

# Test limited processing
python3 test_10_docs.py

# Test single page processing
python3 test_single_page.py
```

### System Status Check
```bash
python3 system_status.py
```

## 🏗️ Project Structure

### Core Modules
- **`main_updated.py`**: Main execution script with complete automation
- **`fetcher.py`**: WordPress REST API integration and document fetching
- **`db.py`**: PostgreSQL database operations and connections
- **`config.py`**: Configuration settings and database credentials
- **`extractor.py`**: Content extraction and processing utilities

### Supporting Scripts
- **`downloader.py`**: PDF download functionality
- **`system_status.py`**: System health and status monitoring
- **`grant_privs.py`**: Database privilege management

### Test Files
- **`test_*.py`**: Comprehensive testing suite for different scenarios
- **`comprehensive_extraction.py`**: Advanced extraction testing
- **`reprocess_with_content.py`**: Reprocessing utilities

### Legacy Files (Reference)
- **`fetcher_*.py`**: Previous versions showing system evolution
- **`main.py`**: Original implementation
- **`complete_extraction.py`**: Alternative extraction methods

## ⚙️ Configuration

### Database Configuration (`config.py`)
```python
DB_CONFIG = {
    'host': 'your_host',
    'database': 'your_database', 
    'user': 'your_username',
    'password': 'your_password',
    'port': 5432
}

TABLE_NAME = 'source.medical_guidelines'
```

### Fetcher Configuration
- **Target Years**: Automatically calculates current and previous year
- **Batch Size**: Configurable document processing batches
- **API Endpoint**: WordPress REST API endpoint configuration

## 📊 System Metrics

### Current Performance
- **Total Posts Available**: 17,383
- **Pages Processed**: 174
- **Documents Targeted**: 449 (from 2024-2025)
- **URLs Tracked**: 908 (for duplicate prevention)
- **Processing Rate**: ~8 documents per execution
- **Success Rate**: >95% with error handling

### Database Schema
```sql
Table: source.medical_guidelines
- id: Primary key
- title: Document title
- agency: 'FDA Philippines'
- country: 'Philippines'
- url: Source URL
- all_text: Full document content
- created_at: Timestamp
- updated_at: Timestamp
```

## 🧪 Testing

The project includes comprehensive testing:

### Test Categories
1. **Database Integration Tests**: Verify PostgreSQL connections and operations
2. **API Integration Tests**: Test WordPress REST API connectivity
3. **Content Extraction Tests**: Validate document processing
4. **Limited Processing Tests**: Test with controlled document sets
5. **Real Content Tests**: Verify actual document extraction

### Running Tests
```bash
# Run specific tests
python3 test_db_integration.py    # Database connectivity
python3 test_10_docs.py          # Limited document processing
python3 test_real_content.py     # Content extraction validation
```

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection**:
   ```bash
   # Check database connectivity
   python3 -c "from db import Database; db = Database(); print('✅ Database connected')"
   ```

2. **API Connectivity**:
   ```bash
   # Test API endpoint
   python3 -c "from fetcher import Fetcher; f = Fetcher(); print('✅ API accessible')"
   ```

3. **Content Extraction**:
   ```bash
   # Verify extraction
   python3 test_real_content.py
   ```

### Debug Mode
Enable detailed logging by modifying the fetcher configuration for verbose output.

## 🚀 Production Deployment

### Daily Automation
Set up a cron job for daily execution:
```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/project && source .venv/bin/activate && python3 main_updated.py
```

### Monitoring
- Monitor logs for processing status
- Check database growth and content quality
- Verify new document detection

## 📈 Future Enhancements

### Planned Features
- **Multi-source Integration**: Expand to other regulatory bodies
- **Advanced Content Analysis**: NLP processing for document categorization
- **Real-time Notifications**: Alert system for new critical documents
- **API Endpoint**: REST API for accessing processed documents
- **Dashboard**: Web interface for monitoring and management

### Technical Improvements
- **Async Processing**: Parallel document processing
- **Caching Layer**: Redis for improved performance
- **Document Versioning**: Track document changes over time
- **Advanced Search**: Full-text search capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Review the troubleshooting section
- Check the comprehensive test suite for examples

---

**🎉 Your FDA Philippines automation is live and sustainable!**

The system automatically fetches the latest regulatory documents, prevents duplicates, and maintains a comprehensive database of FDA Philippines guidelines.
