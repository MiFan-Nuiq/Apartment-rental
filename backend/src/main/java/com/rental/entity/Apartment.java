package com.rental.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;
import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "apartments")
public class Apartment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(length = 200)
    private String address;

    @Column(length = 20)
    private String building;

    @Column(length = 20)
    private String unit;

    @Column(length = 20)
    private String roomNumber;

    @Column(precision = 10, scale = 2)
    private BigDecimal area;

    @Column(precision = 10, scale = 2)
    private BigDecimal monthlyRent;

    @Column(length = 20)
    private String status;

    @Column(length = 500)
    private String description;

    @Column(length = 20)
    private String floor;

    @ManyToOne
    @JoinColumn(name = "landlord_id")
    private User landlord;

    @Column(length = 500)
    private String coverImage;

    @Column(length = 2000)
    private String detailImages;

    @Column(length = 20)
    private String auditStatus;

    @Column(length = 500)
    private String auditRemark;

    @Column(nullable = false, updatable = false)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime createTime;

    private LocalDateTime updateTime;

    @PrePersist
    protected void onCreate() {
        createTime = LocalDateTime.now();
        updateTime = LocalDateTime.now();
        if (auditStatus == null) {
            auditStatus = "待审核";
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updateTime = LocalDateTime.now();
    }
}
