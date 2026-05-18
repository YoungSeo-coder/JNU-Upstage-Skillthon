package com.cnu.cleanalba.domain;

public enum AnswerOption {
    YES("O"),
    NO("X"),
    NOT_APPLICABLE("해당 없음");

    private final String label;

    AnswerOption(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
