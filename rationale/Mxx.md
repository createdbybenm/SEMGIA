# Mxx – Carlos (P3 Azure)

**The choice I support:** the model runs on our laptop, and Azure only stores the recordings and shows them.

Each recording is saved on the laptop first and uploaded to Azure after. I support this because a classroom
Wi-Fi can fail, and a recording that only lived in the cloud would then be lost. On the laptop we also use
the same Python code for training and for the live test, so the model sees the signal in the same way both
times. Azure keeps the metadata of each recording in a table, one row per recording, a bit like a patient
file. My doubt: the free dashboard is slow to wake up, so we must open it before the demo.

**Source:** Microsoft Learn. "What is Azure Table storage?" https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-overview
