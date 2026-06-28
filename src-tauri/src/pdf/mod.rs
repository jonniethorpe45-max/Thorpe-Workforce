use crate::db::DiagnosticReport;
use crate::licensing;
use crate::AppState;
use printpdf::*;
use std::fs::File;
use std::io::BufWriter;
use std::path::{Component, Path, PathBuf};
use tauri::State;

#[tauri::command]
pub fn export_report_pdf(state: State<AppState>, report_id: String, output_path: String) -> Result<String, String> {
    let report = {
        let db = state.lock_db()?;
        licensing::require_feature(&db, "pdf_export")?;
        db.get_report(&report_id).map_err(|e| e.to_string())?
    };
    let validated_path = validate_pdf_output_path(&output_path)?;
    generate_pdf(&report, &validated_path)?;
    Ok(validated_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn export_agent_session_pdf(
    state: State<AppState>,
    session_id: String,
    output_path: String,
) -> Result<String, String> {
    let sessions = {
        let db = state.lock_db()?;
        licensing::require_feature(&db, "pdf_export")?;
        db.list_agent_sessions(200).map_err(|e| e.to_string())?
    };
    let session = sessions
        .into_iter()
        .find(|s| s.id == session_id)
        .ok_or_else(|| "Agent session not found.".to_string())?;
    let validated_path = validate_pdf_output_path(&output_path)?;
    generate_agent_session_pdf(&session, &validated_path)?;
    Ok(validated_path.to_string_lossy().to_string())
}

fn generate_agent_session_pdf(session: &crate::db::AgentSessionRecord, path: &Path) -> Result<(), String> {
    let (doc, page1, layer1) = PdfDocument::new(
        "Thorpe Agent Session Report",
        Mm(210.0),
        Mm(297.0),
        "Layer 1",
    );
    let current_layer = doc.get_page(page1).get_layer(layer1);
    let font = doc.add_builtin_font(BuiltinFont::Helvetica).map_err(|e| e.to_string())?;
    let font_bold = doc.add_builtin_font(BuiltinFont::HelveticaBold).map_err(|e| e.to_string())?;
    let mut y = 280.0;
    current_layer.use_text("THORPE AGENT SESSION", 16.0, Mm(20.0), Mm(y), &font_bold);
    y -= 12.0;
    current_layer.use_text(&format!("Session: {}", session.id), 9.0, Mm(20.0), Mm(y), &font);
    y -= 8.0;
    current_layer.use_text(&format!("Confidence: {:.0}%", session.confidence * 100.0), 11.0, Mm(20.0), Mm(y), &font);
    y -= 12.0;
    current_layer.use_text("USER MESSAGE", 12.0, Mm(20.0), Mm(y), &font_bold);
    y -= 8.0;
    for line in wrap_text(&session.message, 85) {
        current_layer.use_text(&line, 10.0, Mm(20.0), Mm(y), &font);
        y -= 6.0;
    }
    y -= 8.0;
    current_layer.use_text("PLAN", 12.0, Mm(20.0), Mm(y), &font_bold);
    y -= 8.0;
    for line in wrap_text(&session.plan_json, 85) {
        if y < 20.0 { break; }
        current_layer.use_text(&line, 9.0, Mm(20.0), Mm(y), &font);
        y -= 5.0;
    }
    if let Some(evidence) = &session.evidence_json {
        y -= 8.0;
        current_layer.use_text("EVIDENCE", 12.0, Mm(20.0), Mm(y), &font_bold);
        y -= 8.0;
        for line in wrap_text(evidence, 85) {
            if y < 20.0 { break; }
            current_layer.use_text(&line, 8.0, Mm(20.0), Mm(y), &font);
            y -= 5.0;
        }
    }
    let file = File::create(path).map_err(|e| format!("Failed to create PDF: {e}"))?;
    let mut buf_writer = BufWriter::new(file);
    doc.save(&mut buf_writer).map_err(|e| format!("Failed to save PDF: {e}"))?;
    Ok(())
}

pub(crate) fn validate_pdf_output_path(path: &str) -> Result<PathBuf, String> {
    let trimmed = path.trim();
    if trimmed.is_empty() {
        return Err("Output path is required.".to_string());
    }

    let path = Path::new(trimmed);
    if !path.is_absolute() {
        return Err("Output path must be an absolute path.".to_string());
    }

    if path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.eq_ignore_ascii_case("pdf"))
        != Some(true)
    {
        return Err("Output path must use a .pdf extension.".to_string());
    }

    for component in path.components() {
        if matches!(component, Component::ParentDir) {
            return Err("Invalid output path: parent directory traversal is not allowed.".to_string());
        }
    }

    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .ok_or_else(|| "Output path must include a parent directory.".to_string())?;

    if !parent.exists() {
        std::fs::create_dir_all(parent).map_err(|e| format!("Failed to create output directory: {}", e))?;
    }

    Ok(path.to_path_buf())
}

fn generate_pdf(report: &DiagnosticReport, path: &Path) -> Result<(), String> {
    let (doc, page1, layer1) = PdfDocument::new(
        &report.title,
        Mm(210.0),
        Mm(297.0),
        "Layer 1",
    );
    let current_layer = doc.get_page(page1).get_layer(layer1);

    let font = doc
        .add_builtin_font(BuiltinFont::Helvetica)
        .map_err(|e| e.to_string())?;
    let font_bold = doc
        .add_builtin_font(BuiltinFont::HelveticaBold)
        .map_err(|e| e.to_string())?;

    let mut y = 280.0;

    current_layer.use_text("THORPE DIAGNOSTIC REPORT", 18.0, Mm(20.0), Mm(y), &font_bold);
    y -= 12.0;
    current_layer.use_text(&report.title, 12.0, Mm(20.0), Mm(y), &font);
    y -= 10.0;
    current_layer.use_text(&format!("Generated: {}", report.created_at), 9.0, Mm(20.0), Mm(y), &font);
    y -= 15.0;

    current_layer.use_text(&format!("Health Score: {}/100", report.health_score), 14.0, Mm(20.0), Mm(y), &font_bold);
    y -= 8.0;
    current_layer.use_text(&format!("Risk Level: {}", report.risk_level.to_uppercase()), 11.0, Mm(20.0), Mm(y), &font);
    y -= 15.0;

    current_layer.use_text("SUMMARY", 12.0, Mm(20.0), Mm(y), &font_bold);
    y -= 8.0;
    for line in wrap_text(&report.summary, 80) {
        current_layer.use_text(&line, 10.0, Mm(20.0), Mm(y), &font);
        y -= 6.0;
    }
    y -= 8.0;

    current_layer.use_text("PLAIN LANGUAGE EXPLANATION", 12.0, Mm(20.0), Mm(y), &font_bold);
    y -= 8.0;
    for line in wrap_text(&report.plain_language, 80) {
        if y < 20.0 { break; }
        current_layer.use_text(&line, 10.0, Mm(20.0), Mm(y), &font);
        y -= 6.0;
    }
    y -= 8.0;

    if y > 30.0 {
        current_layer.use_text("FINDINGS", 12.0, Mm(20.0), Mm(y), &font_bold);
        y -= 8.0;
        if let Ok(findings) = serde_json::from_str::<Vec<serde_json::Value>>(&report.findings) {
            for finding in findings.iter().take(5) {
                if y < 20.0 { break; }
                let title = finding["title"].as_str().unwrap_or("Unknown");
                let severity = finding["severity"].as_str().unwrap_or("unknown");
                current_layer.use_text(&format!("[{}] {}", severity.to_uppercase(), title), 10.0, Mm(25.0), Mm(y), &font);
                y -= 6.0;
            }
        }
    }

    y -= 10.0;
    if y > 15.0 {
        current_layer.use_text("---", 10.0, Mm(20.0), Mm(y), &font);
        y -= 6.0;
        current_layer.use_text("Generated by Thorpe — AI IT Support Platform", 8.0, Mm(20.0), Mm(y), &font);
        y -= 5.0;
        current_layer.use_text("https://thorpe.app", 8.0, Mm(20.0), Mm(y), &font);
    }

    let file = File::create(path).map_err(|e| format!("Failed to create PDF file: {}", e))?;
    let mut buf_writer = BufWriter::new(file);
    doc.save(&mut buf_writer).map_err(|e| format!("Failed to save PDF: {}", e))?;

    Ok(())
}

fn wrap_text(text: &str, max_chars: usize) -> Vec<String> {
    let mut lines = Vec::new();
    let mut current = String::new();
    for word in text.split_whitespace() {
        if current.len() + word.len() + 1 > max_chars {
            if !current.is_empty() {
                lines.push(current.clone());
            }
            current = word.to_string();
        } else {
            if !current.is_empty() {
                current.push(' ');
            }
            current.push_str(word);
        }
    }
    if !current.is_empty() {
        lines.push(current);
    }
    lines
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_relative_paths() {
        assert!(validate_pdf_output_path("report.pdf").is_err());
    }

    #[test]
    fn rejects_path_traversal() {
        assert!(validate_pdf_output_path("/tmp/../etc/passwd.pdf").is_err());
    }

    #[test]
    fn rejects_non_pdf_extension() {
        assert!(validate_pdf_output_path("/tmp/report.txt").is_err());
    }

    #[test]
    fn accepts_valid_pdf_path() {
        let path = validate_pdf_output_path("/tmp/thorpe-report.pdf").unwrap();
        assert_eq!(path, PathBuf::from("/tmp/thorpe-report.pdf"));
    }
}
