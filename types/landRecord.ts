export type RecordStatus = "Verified" | "Pending" | "Under Review" | "Rejected";

export interface LandRecord {
  id: string;
  ownerName: string;
  guardianName: string;
  village: string;
  district: string;
  state: string;
  khasraNumber: string;
  khatauniNumber: string;
  areaValue: number;
  areaUnit: "Acres" | "Hectares" | "Bigha";
  landType: "Agricultural" | "Residential" | "Commercial" | "Barren";
  status: RecordStatus;
  registrationDate: string; // ISO date
  lastUpdated: string; // ISO date
  documentName: string;
  documentType: "PDF" | "Image";
  documentSizeKb: number;
  mutationNumber: string;
  marketValueInr: number;
}

export interface DashboardStats {
  totalRecords: number;
  verifiedRecords: number;
  pendingRecords: number;
  documentsUploaded: number;
}

export interface RecentUpload {
  id: string;
  fileName: string;
  relatedRecordId: string;
  uploadedAt: string; // ISO date
  sizeKb: number;
  status: "Processed" | "Processing" | "Failed";
}
