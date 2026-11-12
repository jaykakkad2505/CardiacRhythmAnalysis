class AppSession:
    """Holds the in-progress ECG workflow state as the clinician moves
    from Import -> Analysis -> Summary. Reset after a report is saved."""

    def __init__(self):
        self.doctor_id = None
        self.doctor_name = ""
        self.reset_ecg_workflow()

    def reset_ecg_workflow(self):
        self.patient = None
        self.dataset_filename = None
        self.raw_signal = None
        self.sampling_rate = 250
        self.result = None  # dict returned by utils.ecg_processing.process_ecg
