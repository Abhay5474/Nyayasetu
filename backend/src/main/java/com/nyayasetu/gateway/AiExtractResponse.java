package com.nyayasetu.gateway;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record AiExtractResponse(String text, int pageCount, int charCount, String method,
                                List<Integer> ocrPages, String languageHint, List<String> warnings) {}
