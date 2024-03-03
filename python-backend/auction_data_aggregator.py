from collections import defaultdict

class AuctionDataAggregator:
    def __init__(self):
        # Adjusting the default value to store both price and name
        self.item_prices = defaultdict(list)
    
    def process_documents(self, documents):
        """Process all documents to aggregate item prices and their names."""
        for doc in documents:
            for item in doc['items']:
                item_id = int(item['id'])
                # Including the item name alongside its price
                self.item_prices[item_id].append((int(item['price']), item['name']))
    
    def calculate_averages(self):
        """Calculate average prices for all items."""
        averages = []
        for item_id, price_name_pairs in self.item_prices.items():
            total_price = sum(price for price, _ in price_name_pairs)
            average_price = total_price // len(price_name_pairs)
            # Assuming all names for the same ID are identical, so we take the first one
            item_name = price_name_pairs[0][1]
            averages.append({"id": item_id, "price": average_price, "name": item_name})
        
        return averages
    
    def generate_output_document(self, averages, timestamp):
        """Generate the output document with averages and the specified timestamp."""
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