import React, { useState, useRef } from 'react';
import { ProductFormData, ExtractedParameter, StandardCandidate } from '../types/assessment';
import { EMPTY_PRODUCT_FORM, PRODUCT_PRESETS } from '../data/demoData';
import { ExtractedReviewModal } from './ExtractedReviewModal';
import { assessmentService } from '../services/assessmentService';
import {
  UploadCloud,
  FileText,
  Trash2,
  Shield,
  ArrowRight,
  RotateCcw,
  Sparkles,
  Loader2,
  SlidersHorizontal,
  Building2,
  FileCheck,
  Tag,
  Layers,
} from 'lucide-react';

interface AssessmentFormViewProps {
  initialData?: ProductFormData;
  onSubmit: (formData: ProductFormData, reviewedParams?: ExtractedParameter[], selectedStandardId?: string, appId?: string) => void;
}

export const AssessmentFormView: React.FC<AssessmentFormViewProps> = ({
  initialData = EMPTY_PRODUCT_FORM,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<ProductFormData>(initialData);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isDragging, setIsDragging] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [extractedData, setExtractedData] = useState<{
    applicationId: string;
    parameters: ExtractedParameter[];
    candidates: StandardCandidate[];
    missingInfo: string[];
    warnings: string[];
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleChange = (field: keyof ProductFormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const updated = { ...prev };
        delete updated[field];
        return updated;
      });
    }
  };

  const handlePresetSelect = (presetId: string) => {
    const preset = PRODUCT_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setFormData(preset.data);
      setErrors({});
    }
  };

  const handleClearForm = () => {
    setFormData(EMPTY_PRODUCT_FORM);
    setErrors({});
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setErrors((prev) => ({ ...prev, datasheet: 'Only PDF documents are supported.' }));
      return;
    }

    // Auto-infer product name if empty
    const inferredName = formData.name.trim() ? formData.name : file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');

    setFormData((prev) => ({
      ...prev,
      name: inferredName,
      datasheetFile: {
        name: file.name,
        size: file.size,
        uploadedAt: new Date().toISOString(),
        rawFile: file,
      },
    }));

    if (errors.datasheet) {
      setErrors((prev) => {
        const updated = { ...prev };
        delete updated.datasheet;
        return updated;
      });
    }
  };

  const removeFile = () => {
    setFormData((prev) => ({ ...prev, datasheetFile: null }));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleStartExtraction = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { [key: string]: string } = {};

    if (!formData.name.trim()) newErrors.name = 'Product name / description is required';
    if (!formData.category.trim()) newErrors.category = 'Please select a product category';
    if (!formData.manufacturingLocation.trim()) newErrors.manufacturingLocation = 'Manufacturing facility location is required';
    if (!formData.datasheetFile) newErrors.datasheet = 'Please upload product technical documentation (PDF) for automated parameter extraction';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsExtracting(true);
    try {
      const extraction = await assessmentService.startAssessment(formData);
      setExtractedData({
        applicationId: extraction.applicationId,
        parameters: extraction.extractedParameters,
        candidates: extraction.standards,
        missingInfo: extraction.missingInfo,
        warnings: extraction.warnings,
      });
      setShowReviewModal(true);
    } catch (err) {
      console.error('Extraction error:', err);
      // Fallback directly to analysis
      onSubmit(formData);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleReviewConfirm = (reviewedParams: ExtractedParameter[], selectedStandardId: string) => {
    setShowReviewModal(false);
    onSubmit(formData, reviewedParams, selectedStandardId, extractedData?.applicationId);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-card overflow-hidden">
        {/* Form Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Product Assessment</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-brand-50 text-brand-700 border border-brand-200 flex items-center gap-1">
                <Layers className="w-3 h-3" />
                Universal Standards Engine
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload product technical documentation to dynamically extract engineering parameters and identify applicable BIS standards.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            {/* Quick Demo Preset Selector */}
            <div className="relative">
              <select
                onChange={(e) => {
                  if (e.target.value) handlePresetSelect(e.target.value);
                  e.target.value = '';
                }}
                defaultValue=""
                className="text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 rounded-lg border border-slate-200 px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-500 cursor-pointer"
                title="Quick sample products for demonstration"
              >
                <option value="" disabled>
                  ⚡ Sample Presets...
                </option>
                {PRODUCT_PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleClearForm}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 rounded-lg border border-slate-200 transition-colors"
              title="Clear all fields"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* Universal Product Profile Form */}
        <form onSubmit={handleStartExtraction} className="p-6 sm:p-8 space-y-6">
          {/* Row 1: Universal Category & Product Name */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Tag className="w-3.5 h-3.5 text-brand-600" />
                Product Category <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.category}
                onChange={(e) => handleChange('category', e.target.value)}
                className={`w-full px-3.5 py-2.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors ${
                  errors.category ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 bg-white'
                }`}
              >
                <option value="">-- Select Product Category --</option>
                <option value="Household Electrical Appliances">Household Electrical Appliances (e.g. Iron, Heater, Mixer, Fan)</option>
                <option value="Kitchen & Pressure Cookers">Kitchenware & Pressure Cookers</option>
                <option value="Electronics & IT Goods">Electronics & IT Goods (e.g. Adapters, Displays, Devices)</option>
                <option value="Lighting & Luminaires">Lighting & Luminaires (e.g. LED Lamps, Luminaires)</option>
                <option value="Industrial & Power Equipment">Industrial & Power Equipment (e.g. Motors, Pumps)</option>
                <option value="Batteries & Storage">Batteries & Power Systems</option>
                <option value="Chemicals & Construction Materials">Chemicals & Construction Materials</option>
                <option value="Other">Other Manufactured Goods</option>
              </select>
              {errors.category && <p className="text-xs text-rose-500 mt-1">{errors.category}</p>}
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <FileCheck className="w-3.5 h-3.5 text-brand-600" />
                Product Name / Description <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g. Electric Steam Iron 1200W, Domestic Pressure Cooker 5L"
                className={`w-full px-3.5 py-2.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors ${
                  errors.name ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 bg-white'
                }`}
              />
              {errors.name && <p className="text-xs text-rose-500 mt-1">{errors.name}</p>}
            </div>
          </div>

          {/* Row 2: Universal Model & Brand / Manufacturer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Model / Serial / Series Number
              </label>
              <input
                type="text"
                value={formData.modelNumber || ''}
                onChange={(e) => handleChange('modelNumber', e.target.value)}
                placeholder="e.g. MOD-2026-X1 / DLX-750"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Brand / Manufacturer Name
              </label>
              <input
                type="text"
                value={formData.manufacturer || ''}
                onChange={(e) => handleChange('manufacturer', e.target.value)}
                placeholder="e.g. Nova Enterprises Ltd."
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              />
            </div>
          </div>

          {/* Row 3: Manufacturing Facility Location */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-brand-600" />
              Manufacturing Facility Location (Premises) <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={formData.manufacturingLocation}
              onChange={(e) => handleChange('manufacturingLocation', e.target.value)}
              placeholder="e.g. Plot 14, Phase II Industrial Area, Noida, Uttar Pradesh"
              className={`w-full px-3.5 py-2.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors ${
                errors.manufacturingLocation ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 bg-white'
              }`}
            />
            {errors.manufacturingLocation && <p className="text-xs text-rose-500 mt-1">{errors.manufacturingLocation}</p>}
          </div>

          {/* Row 4: PDF Technical Documentation Uploader */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Product Technical Documentation (PDF) <span className="text-rose-500">*</span>
              </label>
              <span className="text-[11px] text-slate-500 flex items-center gap-1 font-medium">
                <SlidersHorizontal className="w-3 h-3 text-brand-600" />
                Technical parameters are extracted dynamically
              </span>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInput}
              accept=".pdf,application/pdf"
              className="hidden"
            />

            {formData.datasheetFile ? (
              <div className="flex items-center justify-between p-4 rounded-xl border border-emerald-200 bg-emerald-50/40">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-900 truncate max-w-xs sm:max-w-md">
                      {formData.datasheetFile.name}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      {formatFileSize(formData.datasheetFile.size)} • PDF Attached & Ready for Dynamic Analysis
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 rounded-md transition-colors"
                  >
                    Replace
                  </button>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md transition-colors"
                    title="Remove file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                  isDragging
                    ? 'border-brand-500 bg-brand-50/50 scale-[0.99]'
                    : 'border-slate-300 hover:border-brand-400 bg-slate-50/50 hover:bg-slate-50'
                } ${errors.datasheet ? 'border-rose-300 bg-rose-50/10' : ''}`}
              >
                <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-3">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <p className="text-sm font-semibold text-slate-800">
                  Click to upload or drag & drop product technical documentation
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Supported format: PDF (Datasheets, Engineering drawings, Test certificates, User manual)
                </p>
              </div>
            )}
            {errors.datasheet && <p className="text-xs text-rose-500 mt-1.5">{errors.datasheet}</p>}
          </div>

          {/* Row 5: Optional Additional Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Additional Engineering Notes / Remarks <span className="text-slate-400 font-normal">(Optional)</span>
            </label>
            <textarea
              rows={2}
              value={formData.additionalNotes || ''}
              onChange={(e) => handleChange('additionalNotes', e.target.value)}
              placeholder="e.g. Certified for Class I operation, internal thermal fuse rating 240°C, stainless steel AISI 304 food-grade..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
            />
          </div>

          {/* Confidentiality Assurance Note */}
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <Shield className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Confidentiality Assurance:</strong> Technical documentation and engineering drawings are analyzed securely for pre-certification evaluation. No proprietary IP is exposed or commited.
            </span>
          </div>

          {/* Primary Action Button */}
          <button
            type="submit"
            disabled={isExtracting}
            className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm text-white bg-brand-600 hover:bg-brand-700 active:bg-brand-800 shadow-md shadow-brand-600/20 hover:shadow-lg transition-all disabled:opacity-75 cursor-pointer"
          >
            {isExtracting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Extracting Technical Parameters & Matching Standards...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Extract & Review Product Specifications</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Extracted Review Modal */}
      {showReviewModal && extractedData && (
        <ExtractedReviewModal
          applicationId={extractedData.applicationId}
          parameters={extractedData.parameters}
          candidates={extractedData.candidates}
          missingInfo={extractedData.missingInfo}
          warnings={extractedData.warnings}
          onConfirm={handleReviewConfirm}
          onClose={() => setShowReviewModal(false)}
        />
      )}
    </div>
  );
};
