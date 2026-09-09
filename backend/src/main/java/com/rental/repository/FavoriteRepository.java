package com.rental.repository;

import com.rental.entity.Favorite;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface FavoriteRepository extends JpaRepository<Favorite, Long> {
    List<Favorite> findByTenantId(Long tenantId);

    Optional<Favorite> findByTenantIdAndApartmentId(Long tenantId, Long apartmentId);

    boolean existsByTenantIdAndApartmentId(Long tenantId, Long apartmentId);

    void deleteByTenantIdAndApartmentId(Long tenantId, Long apartmentId);

    long countByApartmentId(Long apartmentId);
}
