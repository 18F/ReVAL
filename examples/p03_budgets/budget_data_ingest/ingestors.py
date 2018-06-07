import csv

from data_ingest import ingestors

class Ingestor(ingestors.Ingestor):

    def insert_tsv(self):
        file_path = self.ingest_destination('.tsv')
        flat = list(self.flattened_data())
        if flat:
            keys = list(flat[0].keys())
            with open(file_path, 'w') as dest_file:
                writer = csv.DictWriter(dest_file, fieldnames=keys, dialect='excel-tab')
                writer.writeheader()
                writer.writerows(flat)


