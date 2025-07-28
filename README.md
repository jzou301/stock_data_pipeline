# Stock Market Data Analysis Pipeline

## Overview  
This project is a Python-based pipeline designed to ingest, process, and analyze stock market data. It fetches real-time and historical market data for equities and ETFs, computes key technical and fundamental indicators, and stores results in a structured database for further analysis.

## Features  
- Data ingestion using yFinance API for live and historical stock data  
- Calculation of technical indicators such as SMA, EMA, RSI, MACD, Beta  
- Computation of fundamental metrics including P/E ratio, EV/EBIT  
- Database schema design for efficient storage and retrieval of processed data  
- Parallel processing with multithreading to speed up data handling  
- Integration with QuantLib for advanced financial computations  

## Technologies Used  
- Python (pandas, NumPy, yFinance, QuantLib, SQLite, multithreading)  
- SQLite database for data storage  
- Additional libraries: SQLAlchemy for database interaction  
