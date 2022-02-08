class JobStatus:
    # A job is pending if it is not yet submitted
    PENDING = 10
    # A job is queued if it is in the queue on the cluster it is to run on
    QUEUED = 40
    # A job is running if it is currently running on the cluster it is to run on
    RUNNING = 50
    # A job is cancelled if it was queued or running and was then cancelled
    CANCELLED = 70
    # A job is completed if it is finished running on the cluster without error
    COMPLETED = 500

    @staticmethod
    def display_name(status):
        if status == JobStatus.PENDING:
            return 'Pending'
        elif status == JobStatus.QUEUED:
            return 'Queued'
        elif status == JobStatus.RUNNING:
            return 'Running'
        elif status == JobStatus.CANCELLED:
            return 'Cancelled'
        elif status == JobStatus.COMPLETED:
            return 'Completed'
        else:
            return 'Unknown'
