from collections import defaultdict

class AuctionDataAggregator:
    def __init__(self):
        self.item_prices = defaultdict(list)
    
    def process_documents(self, documents):
        """Process all documents to aggregate item prices and Fyr'alath total costs."""
        for doc in documents:
            for item in doc['items']:
                item_id = int(item['id'])
                self.item_prices[item_id].append(int(item['price']))
    
    def calculate_averages(self):
        """Calculate average prices for all items and the average total cost for Fyr'alath."""
        averages = []
        for item_id, prices in self.item_prices.items():
            average_price = sum(prices) // len(prices)
            averages.append({"id": item_id, "price": average_price})
        
        return averages
    
    def generate_output_document(self, averages, timestamp):
        """Generate the output document with averages, the specified timestamp, and Fyr'alath average total cost."""
        output_document = {
            "timestamp": timestamp,
            "items": averages
        }

        return output_document

    def aggregate_data_and_generate_output(self, documents, timestamp):
        """Public method to process input documents and return the final output document."""
        self.process_documents(documents)
        averages = self.calculate_averages()
        return self.generate_output_document(averages, timestamp)